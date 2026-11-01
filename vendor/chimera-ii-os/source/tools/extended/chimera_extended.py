#!/usr/bin/env python3
"""Chimera II OS extended application generator.

Scans every cloned project repository and produces a complete, installable
application payload:

  bin/          launchers for every app (python, java, node, web)
  gui/          generated Tkinter GUI wrappers for command-line Python apps
  pyinstaller/  PyInstaller .spec files (one per app)
  applications/ freedesktop .desktop entries
  nginx/        reverse-proxy snippets (system-user auth via Cockpit)
  systemd/      per-app service units for exposed web apps
  web-apps.json catalogue of exposed web interfaces
  app-catalog.json full application catalogue
  SUMMARY.json  generation summary

Usage:
  chimera_extended.py --repos DIR --out DIR [--build-pyinstaller N]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import sys
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist",
             "build", ".tox", ".mypy_cache", ".pytest_cache", "target"}
PY_GUI_HINTS = ("tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6", "wx.",
                "gi.repository", "kivy", "pygame", "customtkinter", "dearpygui")
WEB_ENTRY = ("index.html", "index.htm", "main.html")
NODE_ENTRY = ("server.js", "index.js", "app.js", "main.js", "cli.js")

WRAPPER = '''#!/usr/bin/env python3
"""Auto-generated Chimera GUI wrapper for __NAME__.

Runs the original command-line program and streams its output into a
Tkinter window with Start / Stop / Clear controls.
"""
import os
import shlex
import subprocess
import sys
import threading

try:
    import tkinter as tk
    from tkinter import scrolledtext
except Exception:
    sys.stderr.write("tkinter unavailable; running in terminal\\n")
    os.execvp("sh", ["sh", "-c", " ".join(shlex.quote(a) for a in ARGV)])

TARGET = __TARGET__
WORKDIR = __WORKDIR__
TITLE = __TITLE__

ARGV = [sys.executable, TARGET]


class App:
    def __init__(self, root):
        self.root = root
        self.proc = None
        root.title("Chimera - " + TITLE)
        root.geometry("900x600")
        bar = tk.Frame(root)
        bar.pack(fill="x", padx=8, pady=6)
        tk.Button(bar, text="Run", command=self.start).pack(side="left")
        tk.Button(bar, text="Stop", command=self.stop).pack(side="left", padx=4)
        tk.Button(bar, text="Clear", command=self.clear).pack(side="left")
        self.status = tk.Label(bar, text="idle", anchor="e")
        self.status.pack(side="right")
        self.out = scrolledtext.ScrolledText(root, bg="#0b0e14", fg="#9fe6a0",
                                             insertbackground="#9fe6a0")
        self.out.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def clear(self):
        self.out.delete("1.0", "end")

    def start(self):
        if self.proc and self.proc.poll() is None:
            return
        self.out.insert("end", "$ " + " ".join(shlex.quote(a) for a in ARGV) + "\\n")
        try:
            self.proc = subprocess.Popen(ARGV, cwd=WORKDIR, stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT, text=True, bufsize=1)
        except Exception as exc:
            self.out.insert("end", "[launch error] " + str(exc) + "\\n")
            return
        self.status.configure(text="running")
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self):
        for line in self.proc.stdout:
            self.out.insert("end", line)
            self.out.see("end")
        rc = self.proc.wait()
        self.status.configure(text="Finished (exit %s)" % rc)

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            self.status.configure(text="stopped")


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
'''

SPEC = '''# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Chimera II OS application: __NAME__
# Build with:  pyinstaller --clean --noconfirm __SPEC__
block_cipher = None

a = Analysis([__TARGET__],
             pathex=[__WORKDIR__],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
          name=__NAME_SAFE__,
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          console=False)
'''


def slug(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip("-").lower()
    return s[:90] or "app"


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            yield Path(dirpath) / fn


def is_gui_python(path: Path) -> bool:
    try:
        head = path.read_text(errors="ignore")[:20000]
    except Exception:
        return False
    return any(h in head for h in PY_GUI_HINTS)


def discover(repos_dir: Path):
    apps = []
    seen = set()
    for repo in sorted(p for p in repos_dir.iterdir() if p.is_dir()):
        rname = repo.name
        for f in iter_files(repo):
            rel = f.relative_to(repo)
            low = f.name.lower()
            kind = None
            if low.endswith(".py") and f.name not in ("setup.py", "conftest.py"):
                kind = "python-gui" if is_gui_python(f) else "python-cli"
            elif low.endswith(".java"):
                kind = "java"
            elif low.endswith(".html") and low in WEB_ENTRY:
                kind = "web-static"
            elif low.endswith(".js") and low in NODE_ENTRY:
                if any((p / "package.json").exists() for p in [f.parent, repo]):
                    kind = "node"
            if not kind:
                continue
            key = (rname, str(rel))
            if key in seen:
                continue
            seen.add(key)
            app_id = slug("%s__%s" % (rname, str(rel).replace(os.sep, "_")))
            apps.append({
                "id": app_id,
                "repo": rname,
                "relpath": str(rel),
                "source": str(f),
                "kind": kind,
                "kind_label": {"python-gui": "Python GUI", "python-cli": "Python CLI",
                               "java": "Java", "node": "Node.js",
                               "web-static": "Web UI"}[kind],
            })
    return apps


def write_exec(path: Path, body: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    path.chmod(0o755)


def gen(apps, out: Path, build_pyinstaller: int):
    for sub in ("bin", "gui", "pyinstaller", "applications", "nginx", "systemd", "config"):
        (out / sub).mkdir(parents=True, exist_ok=True)

    counts = {}
    web = []
    port = 8100

    for a in apps:
        kind = a["kind"]
        counts[kind] = counts.get(kind, 0) + 1
        src = Path(a["source"])
        workdir = str(src.parent)
        name = a["relpath"]
        app_id = a["id"]

        if kind == "python-cli":
            body = (WRAPPER.replace("__NAME__", name)
                           .replace("__TARGET__", repr(str(src)))
                           .replace("__WORKDIR__", repr(workdir))
                           .replace("__TITLE__", repr(name)))
            write_exec(out / "gui" / (app_id + ".py"), body)
            a["command"] = "/opt/chimera/apps/gui/%s.py" % app_id
            a["gui"] = True
        elif kind in ("python-gui", "java"):
            a["command"] = "/opt/chimera/apps/bin/%s" % app_id
            a["gui"] = True
        elif kind == "node":
            a["command"] = "/opt/chimera/apps/bin/%s" % app_id
            a["gui"] = False
        else:
            a["command"] = None
            a["gui"] = False

        if a.get("command"):
            if kind == "python-gui":
                body = "#!/bin/sh\nexec python3 %s \"$@\"\n" % shlex.quote(str(src))
            elif kind == "java":
                body = ("#!/bin/sh\n# Java launcher for %s\n"
                        "cd %s || exit 1\n"
                        "if ls *.jar >/dev/null 2>&1; then exec java -jar *.jar \"$@\"; fi\n"
                        "if command -v javac >/dev/null 2>&1; then\n"
                        "  mkdir -p /tmp/chimera-java && javac -d /tmp/chimera-java %s 2>/dev/null && "
                        "exec java -cp /tmp/chimera-java %s \"$@\"\n"
                        "fi\nexec java %s \"$@\"\n") % (
                            name, shlex.quote(workdir), shlex.quote(src.name),
                            src.stem, src.stem)
            else:
                body = "#!/bin/sh\ncd %s || exit 1\nexec node %s \"$@\"\n" % (
                    shlex.quote(workdir), shlex.quote(str(src)))
            write_exec(out / "bin" / app_id, body)

        if kind in ("python-cli", "python-gui"):
            target = out / "gui" / (app_id + ".py") if kind == "python-cli" else src
            spec = (SPEC.replace("__NAME__", name)
                        .replace("__SPEC__", app_id + ".spec")
                        .replace("__TARGET__", repr(str(target)))
                        .replace("__WORKDIR__", repr(workdir))
                        .replace("__NAME_SAFE__", repr(app_id)))
            (out / "pyinstaller" / (app_id + ".spec")).write_text(spec)

        if a.get("command"):
            cat = "Development;" if kind in ("python-cli", "java", "node") else "Utility;"
            if kind == "python-gui":
                cat = "Utility;Development;"
            (out / "applications" / ("chimera-%s.desktop" % app_id)).write_text(
                "[Desktop Entry]\nType=Application\nVersion=1.0\nName=%s\n"
                "Comment=%s from %s\nExec=%s\nIcon=applications-development\n"
                "Terminal=false\nCategories=%s\nKeywords=chimera;%s;%s;\n" % (
                    name, a["kind_label"], a["repo"], a["command"], cat,
                    a["repo"].lower(), kind))

        if kind == "web-static":
            port += 1
            root = str(src.parent)
            conf = ("location /apps/%s/ {\n"
                    "    alias %s/;\n"
                    "    index index.html;\n"
                    "    auth_request /_chimera_auth;\n"
                    "}\n") % (app_id, root)
            (out / "nginx" / (app_id + ".conf")).write_text(conf)
            web.append({"id": app_id, "repo": a["repo"], "path": "/apps/%s/" % app_id,
                        "root": root, "port": port, "auth": "system-users"})
        elif kind == "node":
            port += 1
            conf = ("location /apps/%s/ {\n"
                    "    proxy_pass http://127.0.0.1:%d/;\n"
                    "    proxy_set_header Host $host;\n"
                    "    auth_request /_chimera_auth;\n"
                    "}\n") % (app_id, port)
            (out / "nginx" / (app_id + ".conf")).write_text(conf)
            (out / "systemd" / ("chimera-app-%s.service" % app_id)).write_text(
                "[Unit]\nDescription=Chimera Node app %s\nAfter=network.target\n\n"
                "[Service]\nType=simple\nWorkingDirectory=%s\n"
                "ExecStart=/usr/bin/node %s\nRestart=on-failure\n\n"
                "[Install]\nWantedBy=multi-user.target\n" % (app_id, workdir, src))
            web.append({"id": app_id, "repo": a["repo"], "path": "/apps/%s/" % app_id,
                        "port": port, "auth": "system-users"})

    (out / "web-apps.json").write_text(json.dumps(web, indent=1))
    (out / "app-catalog.json").write_text(json.dumps(apps, indent=1))

    summary = {
        "repositories": sorted({a["repo"] for a in apps}),
        "applications": len(apps),
        "by_kind": counts,
        "gui_wrappers": counts.get("python-cli", 0),
        "pyinstaller_specs": counts.get("python-cli", 0) + counts.get("python-gui", 0),
        "web_exposed": len(web),
        "pyinstaller_built": 0,
    }

    if build_pyinstaller > 0 and shutil.which("pyinstaller"):
        built = 0
        import subprocess
        for spec in sorted((out / "pyinstaller").glob("*.spec")):
            if built >= build_pyinstaller:
                break
            try:
                r = subprocess.run(["pyinstaller", "--clean", "--noconfirm",
                                    "--distpath", str(out / "pyinstaller" / "dist"),
                                    "--workpath", "/tmp/pyi-work",
                                    "--specpath", str(out / "pyinstaller"),
                                    str(spec)],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   timeout=120)
                if r.returncode == 0:
                    built += 1
            except Exception:
                continue
        summary["pyinstaller_built"] = built

    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1))
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repos", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--build-pyinstaller", type=int, default=0)
    args = ap.parse_args()

    repos = Path(args.repos)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    apps = discover(repos)
    print("discovered %d applications across %d repositories" % (
        len(apps), len({a['repo'] for a in apps})))
    summary = gen(apps, out, args.build_pyinstaller)
    print("done:", summary["by_kind"])
    print("web exposed:", summary["web_exposed"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
