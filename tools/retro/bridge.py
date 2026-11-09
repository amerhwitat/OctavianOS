#!/usr/bin/env python3
"""Loopback-only launcher bridge for Amiga and Commodore emulators.

Firmware and disk images are user supplied. This bridge launches installed
emulator binaries; it does not download ROMs or execute shell command strings.
"""
import json
import os
import shutil
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "127.0.0.1"
PORT = 8766
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
AMIGA_CORE = os.path.join(ROOT, ".local", "retro", "cores", "puae_libretro.so")
COMMODORE = {
    "c64": ("x64sc", {".d64", ".g64", ".crt", ".prg", ".t64", ".tap", ".zip"}),
    "c128": ("x128", {".d64", ".d71", ".d81", ".prg", ".t64", ".tap", ".crt", ".zip"}),
    "vic20": ("xvic", {".d64", ".prg", ".crt", ".tap", ".zip"}),
    "plus4": ("xplus4", {".d64", ".prg", ".crt", ".tap", ".zip"}),
    "pet": ("xpet", {".d64", ".prg", ".crt", ".zip"}),
}
AMIGA_FORMATS = {".adf", ".adz", ".dms", ".fdi", ".ipf", ".hdf", ".hdz",
                 ".lha", ".zip", ".m3u", ".iso", ".cue", ".chd"}


def local_file(value, allowed):
    path = os.path.realpath(os.path.expanduser(str(value or "").strip()))
    if not path:
        raise ValueError("content path required")
    if not os.path.isfile(path):
        raise FileNotFoundError("content file not found")
    if os.path.splitext(path)[1].lower() not in allowed:
        raise TypeError("unsupported content format")
    return path


def respond(handler, status, payload):
    raw = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(raw)))
    handler.send_header("Access-Control-Allow-Origin", "https://amerhwitat.github.io")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    if raw:
        handler.wfile.write(raw)


class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        respond(self, 204, {})

    def do_GET(self):
        if self.path != "/health":
            return respond(self, 404, {"error": "not-found"})
        respond(self, 200, {
            "ok": True,
            "service": "octavian-retro-bridge/1",
            "amiga_core": os.path.isfile(AMIGA_CORE),
            "vice": {model: shutil.which(provider) is not None
                     for model, (provider, _) in COMMODORE.items()},
        })

    def do_POST(self):
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size < 0 or size > 16384:
                return respond(self, 413, {"error": "request too large"})
            data = json.loads(self.rfile.read(size) or b"{}")
            if self.path == "/launch/amiga":
                if not os.path.isfile(AMIGA_CORE):
                    return respond(self, 409, {
                        "error": "PUAE libretro core not built",
                        "expected": AMIGA_CORE,
                    })
                content = local_file(data.get("content"), AMIGA_FORMATS)
                retroarch = shutil.which("retroarch")
                if not retroarch:
                    return respond(self, 409, {"error": "RetroArch not installed"})
                command = [retroarch, "-L", AMIGA_CORE, content]
                subprocess.Popen(command, start_new_session=True)
                return respond(self, 200, {"ok": True, "provider": "PUAE", "command": command})

            if self.path == "/launch/commodore":
                model = str(data.get("model", "c64")).strip().lower()
                if model not in COMMODORE:
                    return respond(self, 400, {"error": "unsupported Commodore model",
                                                "supported": sorted(COMMODORE)})
                provider, formats = COMMODORE[model]
                emulator = shutil.which(provider)
                if not emulator:
                    return respond(self, 409, {"error": "VICE emulator not installed",
                                                "provider": provider})
                content = local_file(data.get("content"), formats)
                command = [emulator, "-autostart", content]
                subprocess.Popen(command, start_new_session=True)
                return respond(self, 200, {"ok": True, "model": model,
                                           "provider": provider, "command": command})
            return respond(self, 404, {"error": "not-found"})
        except ValueError as exc:
            return respond(self, 400, {"error": str(exc)})
        except FileNotFoundError as exc:
            return respond(self, 404, {"error": str(exc)})
        except TypeError as exc:
            return respond(self, 415, {"error": str(exc)})
        except (json.JSONDecodeError, UnicodeDecodeError):
            return respond(self, 400, {"error": "invalid JSON request"})

    def log_message(self, fmt, *args):
        print(fmt % args)


if __name__ == "__main__":
    print(f"Octavian retro bridge listening on http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
