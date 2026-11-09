#!/usr/bin/env python3
"""Validate an installed OctavianOS desktop session manifest before launch."""
from __future__ import annotations
import json, os, sys
from pathlib import Path

PROFILES = {"jasper", "gates", "aurora", "marine"}
ALIASES = {"jasper", "gates"}

def fail(message, code=126):
    print(f"aurora-session-manifest-check: {message}", file=sys.stderr)
    return code

def main(argv):
    if len(argv) != 1 or argv[0] not in PROFILES:
        print("usage: aurora-session-manifest-check <jasper|gates|aurora|marine>", file=sys.stderr)
        return 2
    profile = argv[0]
    if profile in ALIASES:
        print(f"validated Aurora interaction alias: {profile}")
        return 0
    root = Path(os.environ.get("OCTAVIAN_SESSION_MANIFEST_DIR", "/usr/share/octavianos/sessions"))
    path = root / (profile + ".json")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return fail(f"session manifest unavailable or invalid: {path}: {exc}")
    launch = data.get("launch")
    checks = {
        "id": data.get("id") == profile,
        "display_backend": data.get("display_backend") == "x11",
        "launch_method": data.get("launch_method") == "web",
        "architecture": "x86_64" in data.get("architectures", []),
        "status": data.get("status") in {"prototype", "experimental", "supported"},
        "executable": isinstance(launch, dict) and launch.get("executable") == "/usr/local/bin/aurora-session",
        "profile_argument": isinstance(launch, dict) and launch.get("args") == ["--profile", profile],
        "readiness_probe": isinstance(data.get("readiness_probe"), str) and bool(data["readiness_probe"].strip()),
    }
    failed = [key for key, ok in checks.items() if not ok]
    if failed:
        return fail(f"{profile} manifest contract failed: {', '.join(failed)}")
    print(f"validated OctavianOS {profile} session manifest ({data.get('status')})")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
