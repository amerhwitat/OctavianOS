#!/usr/bin/env python3
"""Package curated Python apps as standalone PyInstaller executables.

Reads ``pyinstaller-targets.json``, runs PyInstaller ``--onefile`` for each
target, and copies the resulting binary into ``apps/bin/``. A manifest is
written to ``desktop/pyinstaller_apps.json``.

Targets whose script is missing are reported and skipped, so the build stays
green while repositories evolve.

Usage:
    build_pyinstaller_apps.py --repos /workspace/repos \
        --targets tools/repos/pyinstaller-targets.json --out apps/bin
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repos", default="/workspace/repos")
    ap.add_argument("--targets", default="tools/repos/pyinstaller-targets.json")
    ap.add_argument("--out", default="apps/bin")
    ap.add_argument("--index", default="desktop/pyinstaller_apps.json")
    ap.add_argument("--work", default="build/pyinstaller")
    ap.add_argument("--only", default=None, help="comma separated target ids")
    args = ap.parse_args()

    if not shutil.which("pyinstaller"):
        print("error: pyinstaller not installed (pip install pyinstaller)", file=sys.stderr)
        return 2

    cfg = json.loads(Path(args.targets).read_text())
    repos_root = Path(args.repos).resolve()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)
    only = set(args.only.split(",")) if args.only else None

    results = []
    for t in cfg["targets"]:
        if only and t["id"] not in only:
            continue
        script = Path(t["script"])
        if not script.is_absolute():
            script = repos_root / t["script"]
        if not script.is_file():
            results.append({**t, "status": "missing", "reason": f"not found: {script}"})
            print(f"  [MISS] {t['id']:24s} {t['script']}")
            continue

        bdir = (work / t["id"]).resolve()
        cmd = [
            "pyinstaller", "--noconfirm", "--clean", "--onefile",
            "--name", t["name"],
            "--distpath", str(bdir / "dist"),
            "--workpath", str(bdir / "work"),
            "--specpath", str(bdir),
            "--paths", str(script.parent),
        ]
        if not t.get("console", False):
            cmd.append("--noconsole")
        for h in t.get("hidden", []):
            cmd += ["--hidden-import", h]
        cmd.append(str(script))

        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(script.parent))
        binary = bdir / "dist" / t["name"]
        if proc.returncode != 0 or not binary.is_file():
            tail = (proc.stderr or proc.stdout or "").strip().splitlines()
            results.append({**t, "status": "fail",
                            "reason": tail[-1][:300] if tail else "pyinstaller failed"})
            print(f"  [FAIL] {t['id']:24s} {results[-1]['reason']}")
            continue

        target = out / t["name"]
        shutil.copy2(binary, target)
        target.chmod(0o755)
        size = target.stat().st_size
        results.append({**t, "status": "ok", "binary": str(target), "bytes": size})
        print(f"  [ OK ] {t['id']:24s} {size / 1e6:6.1f} MB -> {target}")

    ok = [r for r in results if r["status"] == "ok"]
    Path(args.index).write_text(json.dumps({
        "schema": "octavianos.pyinstaller-apps/1",
        "total": len(results),
        "built": len(ok),
        "bytes": sum(r["bytes"] for r in ok),
        "apps": results,
    }, indent=2) + "\n")
    print(f"\nbuilt {len(ok)}/{len(results)} executables -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
