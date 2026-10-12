#!/usr/bin/env python3
"""Verify the OctavianOS first-class entry point delegates to the vendored runtime."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTRY = ROOT / "tools" / "chimera" / "chimera-hosted"


def main() -> int:
    cases = [
        (("info",), "json"),
        (("compat", "list"), "json"),
        (("translate", "--mode", "windows", "ls"), "json"),
        (("run", "--mode", "linux", "--", "echo", "octavian-entry-ok"), "text"),
    ]
    for args, kind in cases:
        result = subprocess.run(
            [sys.executable, str(ENTRY), *args],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )
        if result.returncode:
            print(f"FAIL {args}: {result.stderr}", file=sys.stderr)
            return 1
        if kind == "json":
            try:
                json.loads(result.stdout)
            except json.JSONDecodeError as exc:
                print(f"FAIL {args}: expected JSON output: {exc}", file=sys.stderr)
                return 1
        elif "octavian-entry-ok" not in result.stdout:
            print(f"FAIL {args}: unexpected output {result.stdout!r}", file=sys.stderr)
            return 1
        print("PASS " + " ".join(args))
    print("PASS OctavianOS hosted entry point")
    print("LIMIT this test does not claim bare-metal boot or guest ISA execution")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
