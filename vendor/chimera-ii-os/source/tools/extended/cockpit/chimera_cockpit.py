#!/usr/bin/env python3
"""Chimera II OS Cockpit-style administration console.

A lightweight RHEL-Cockpit-like web console. Authentication uses real system
users: PAM (libpam via ctypes) when available, with a /etc/shadow crypt(3)
fallback. It also exposes ``/auth`` which nginx uses as ``auth_request`` for
every exposed application, so all app/web UIs share the system-user login.

Run:  chimera_cockpit.py --port 9090
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.util
import hashlib
import hmac
import json
import os
import platform
import pwd
import shlex
import shutil
import socket
import subprocess
import time

try:
    from flask import Flask, Response, request, session, redirect
except Exception:  # pragma: no cover
    Flask = None

APP = Flask(__name__) if Flask else None
SECRET_FILE = "/etc/chimera/cockpit.secret"


def _secret():
    try:
        with open(SECRET_FILE, "rb") as f:
            return f.read()
    except Exception:
        s = os.urandom(32)
        try:
            os.makedirs("/etc/chimera", exist_ok=True)
            with open(SECRET_FILE, "wb") as f:
                f.write(s)
            os.chmod(SECRET_FILE, 0o600)
        except Exception:
            pass
        return s


# ---------------------------------------------------------------- auth
def pam_authenticate(user: str, password: str) -> bool:
    """Authenticate against PAM using ctypes (no external modules)."""
    try:
        libname = ctypes.util.find_library("pam") or "libpam.so.0"
        pam = ctypes.CDLL(libname)
    except Exception:
        return False

    class PamMessage(ctypes.Structure):
        _fields_ = [("msg_style", ctypes.c_int), ("msg", ctypes.c_char_p)]

    class PamResponse(ctypes.Structure):
        _fields_ = [("resp", ctypes.c_char_p), ("resp_retcode", ctypes.c_int)]

    PAM_PROMPT_ECHO_OFF = 1
    PAM_SUCCESS = 0

    def conv(n, msg, resp, data):
        arr = ctypes.cast(resp, ctypes.POINTER(ctypes.POINTER(PamResponse)))
        out = (PamResponse * n)()
        for i in range(n):
            m = msg[i]
            if m.msg_style == PAM_PROMPT_ECHO_OFF:
                out[i].resp = ctypes.c_char_p(password.encode())
                out[i].resp_retcode = 0
        arr[0] = ctypes.cast(out, ctypes.POINTER(PamResponse))
        return PAM_SUCCESS

    CONV = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int,
                            ctypes.POINTER(PamMessage),
                            ctypes.POINTER(ctypes.POINTER(PamResponse)),
                            ctypes.c_void_p)
    conv_fn = CONV(conv)

    class PamConv(ctypes.Structure):
        _fields_ = [("conv", CONV), ("appdata_ptr", ctypes.c_void_p)]

    pc = PamConv(conv_fn, None)
    handle = ctypes.c_void_p()
    try:
        if pam.pam_start(b"login", user.encode(), ctypes.byref(pc),
                         ctypes.byref(handle)) != PAM_SUCCESS:
            return False
        rc = pam.pam_authenticate(handle, 0)
        pam.pam_end(handle, rc)
        return rc == PAM_SUCCESS
    except Exception:
        return False


def shadow_authenticate(user: str, password: str) -> bool:
    """Fallback: verify against /etc/shadow using crypt(3)."""
    try:
        with open("/etc/shadow") as f:
            for line in f:
                parts = line.strip().split(":")
                if len(parts) < 2 or parts[0] != user:
                    continue
                stored = parts[1]
                if not stored or stored[0] not in "$y$":
                    pass
                if stored in ("!", "*", "!!", ""):
                    return False
                try:
                    import crypt
                    return hmac.compare_digest(crypt.crypt(password, stored), stored)
                except Exception:
                    # glibc >= 2.28 removed crypt(); try openssl passwd
                    algo = "-6"
                    if stored.startswith("$y$"):
                        algo = "-6"
                    r = subprocess.run(["openssl", "passwd", algo, "-salt",
                                        stored.split("$")[2] if "$" in stored else "xx",
                                        password],
                                       stdout=subprocess.PIPE, text=True)
                    return r.returncode == 0 and r.stdout.strip() == stored
    except PermissionError:
        return False
    except Exception:
        return False
    return False


def authenticate(user: str, password: str) -> bool:
    if not user or not password:
        return False
    try:
        pwd.getpwnam(user)
    except KeyError:
        return False
    return pam_authenticate(user, password) or shadow_authenticate(user, password)


# ---------------------------------------------------------------- system info
def _read(path, default=""):
    try:
        with open(path) as f:
            return f.read().strip()
    except Exception:
        return default


def system_info():
    total = avail = 0
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    total = int(line.split()[1]) * 1024
                elif line.startswith("MemAvailable:"):
                    avail = int(line.split()[1]) * 1024
    except Exception:
        pass
    du = shutil.disk_usage("/")
    return {
        "hostname": socket.gethostname(),
        "kernel": platform.release(),
        "os": _read("/etc/os-release").replace("\n", " ")[:200],
        "uptime_s": float(_read("/proc/uptime", "0 0").split()[0] or 0),
        "cpus": os.cpu_count(),
        "mem_total": total,
        "mem_available": avail,
        "disk_total": du.total,
        "disk_free": du.free,
        "load": _read("/proc/loadavg"),
        "users": [p.pw_name for p in pwd.getpwall() if 1000 <= p.pw_uid < 60000],
    }


def run(cmd, timeout=10):
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, timeout=timeout)
        return p.returncode, p.stdout
    except Exception as exc:
        return 1, str(exc)


# ---------------------------------------------------------------- routes
if APP:
    APP.secret_key = _secret()

    def logged_in():
        return bool(session.get("user"))

    @APP.route("/auth", methods=["GET", "POST"])
    def auth_request():
        """nginx auth_request endpoint: 200 if the session is valid."""
        if logged_in():
            return Response("ok", status=200)
        return Response("unauthorized", status=401,
                        headers={"WWW-Authenticate": 'Basic realm="Chimera"'})

    @APP.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            u = request.form.get("user", "")
            p = request.form.get("password", "")
            if authenticate(u, p):
                session["user"] = u
                return redirect("/")
            return Response("Invalid credentials", status=401)
        return Response(LOGIN_HTML, mimetype="text/html")

    @APP.route("/logout")
    def logout():
        session.clear()
        return redirect("/login")

    @APP.route("/health")
    def health():
        return Response(json.dumps({"status": "ok", "auth": "pam+shadow"}),
                        mimetype="application/json")

    @APP.route("/api/info")
    def api_info():
        if not logged_in():
            return Response("unauthorized", status=401)
        return Response(json.dumps(system_info()), mimetype="application/json")

    @APP.route("/api/services")
    def api_services():
        if not logged_in():
            return Response("unauthorized", status=401)
        rc, out = run(["systemctl", "list-units", "--type=service",
                       "--no-pager", "--no-legend"])
        return Response(out, mimetype="text/plain")

    @APP.route("/api/logs")
    def api_logs():
        if not logged_in():
            return Response("unauthorized", status=401)
        rc, out = run(["journalctl", "-n", "200", "--no-pager"])
        return Response(out, mimetype="text/plain")

    @APP.route("/")
    def index():
        if not logged_in():
            return redirect("/login")
        info = system_info()
        return Response(INDEX_HTML.replace("__INFO__", json.dumps(info)),
                        mimetype="text/html")


LOGIN_HTML = """<!doctype html><html><head><meta charset="utf-8">
<title>Chimera II OS - Console Login</title>
<style>body{background:#0b0e14;color:#e8ecf4;font-family:system-ui;display:flex;
align-items:center;justify-content:center;height:100vh;margin:0}
form{background:#131a24;padding:32px;border-radius:12px;width:320px}
h1{color:#7fd1ff;font-size:20px;margin:0 0 16px}
input{width:100%;padding:10px;margin:6px 0;background:#0b0e14;border:1px solid #24303f;
color:#e8ecf4;border-radius:6px}button{width:100%;padding:10px;margin-top:12px;
background:#2b7de9;color:#fff;border:0;border-radius:6px;font-weight:600}
p{color:#6b7a90;font-size:12px}</style></head><body>
<form method="post" action="/login"><h1>Chimera II OS Console</h1>
<input name="user" placeholder="System username" autofocus>
<input name="password" type="password" placeholder="Password">
<button type="submit">Sign in</button>
<p>Authentication uses your system account (PAM / shadow).</p></form></body></html>"""

INDEX_HTML = """<!doctype html><html><head><meta charset="utf-8">
<title>Chimera II OS Console</title>
<style>body{background:#0b0e14;color:#e8ecf4;font-family:system-ui;margin:0;padding:24px}
h1{color:#7fd1ff}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}
.card{background:#131a24;border-radius:10px;padding:16px}pre{white-space:pre-wrap;font-size:12px;
color:#9fe6a0;max-height:300px;overflow:auto}a{color:#9fe6a0}</style></head><body>
<h1>Chimera II OS Console</h1><p><a href="/logout">Sign out</a></p>
<div class="grid" id="g"></div>
<pre id="log">loading...</pre>
<script>
const info = __INFO__;
const g = document.getElementById('g');
const fmt = n => (n/1073741824).toFixed(1)+' GiB';
for (const [k,v] of Object.entries({Host:info.hostname,Kernel:info.kernel,CPUs:info.cpus,
 'Memory':fmt(info.mem_total),'Free disk':fmt(info.disk_free),'Load':info.load})) {
  const d=document.createElement('div');d.className='card';
  d.innerHTML='<div style="color:#6b7a90;font-size:12px">'+k+'</div><div style="font-size:20px">'+v+'</div>';
  g.appendChild(d);
}
fetch('/api/logs').then(r=>r.text()).then(t=>document.getElementById('log').textContent=t);
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=int(os.environ.get("CHIMERA_COCKPIT_PORT", "9090")))
    ap.add_argument("--host", default="0.0.0.0")
    args = ap.parse_args()
    if APP is None:
        print("Flask is required: pip install flask", flush=True)
        return 1
    APP.run(host=args.host, port=args.port, threaded=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
