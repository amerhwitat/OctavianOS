#!/usr/bin/env python3
"""Smoke-test the vendored Chimera II hosted runtime as OctavianOS tooling.

These tests prove the hosted bridge can run on the CI host. They do not claim
that Koronos boots, a guest ISA executes, or the bare-metal OS is complete.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "vendor" / "chimera-ii-os" / "source"
RUNTIME = SOURCE / "tools" / "runtime" / "chimera-hosted.py"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RUNTIME), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=15,
    )


def main() -> int:
    required = [
        RUNTIME,
        SOURCE / "tools" / "chimera-toolchain" / "CMakeLists.txt",
        SOURCE / "lib" / "chimera-nbit",
        SOURCE / "kernel",
        SOURCE / "boot",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        print("Missing required vendored source paths:", *missing, sep="\n  ", file=sys.stderr)
        return 1

    checks = [
        ("info", ("info",)),
        ("compatibility matrix", ("compat", "list")),
        ("host ISA inventory", ("isa",)),
        ("Windows alias translation", ("translate", "--mode", "windows", "ls")),
        ("safe built-in command", ("run", "--mode", "linux", "--", "echo", "octavian-bridge-ok")),
    ]
    for label, args in checks:
        result = run(*args)
        if result.returncode != 0:
            print(f"FAIL {label}: exit={result.returncode}\n{result.stderr}", file=sys.stderr)
            return 1
        if label in {"info", "compatibility matrix", "host ISA inventory", "Windows alias translation"}:
            try:
                payload = json.loads(result.stdout)
            except json.JSONDecodeError as exc:
                print(f"FAIL {label}: output is not JSON: {exc}", file=sys.stderr)
                return 1
            if not isinstance(payload, dict):
                print(f"FAIL {label}: expected JSON object", file=sys.stderr)
                return 1
        elif "octavian-bridge-ok" not in result.stdout:
            print(f"FAIL {label}: unexpected output {result.stdout!r}", file=sys.stderr)
            return 1
        print(f"PASS {label}")

    alias = json.loads(run("translate", "--mode", "windows", "ls").stdout)
    if alias.get("canonical") != "dir" or not alias.get("alias_applied"):
        print(f"FAIL Windows ls alias mapping: {alias}", file=sys.stderr)
        return 1

    print("PASS vendored Chimera II hosted bridge is runnable on this host")
    print("LIMIT bare-metal boot, guest ISA execution, and GUI readiness are not tested here")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
