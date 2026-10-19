#!/usr/bin/env python3
"""Fail-closed six-case production userspace acceptance matrix.

Expected trace names are <target>-<firmware>.log, where target is live,
installer, or recovery and firmware is bios or uefi. This wrapper deliberately
delegates all per-trace semantics to the unchanged production verifier.
Missing traces are failures, not skips. Test-only fixtures are not accepted.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

TARGETS = ("live", "installer", "recovery")
FIRMWARES = ("bios", "uefi")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace_dir", type=Path)
    args = parser.parse_args()

    verifier = Path(__file__).with_name("verify-userspace-handoff.py")
    failures = 0
    for target in TARGETS:
        for firmware in FIRMWARES:
            trace = args.trace_dir / f"{target}-{firmware}.log"
            case = f"{target.upper()} / {firmware.upper()}"
            if not trace.is_file() or trace.stat().st_size == 0:
                print(f"FAIL {case}: required production trace missing: {trace}")
                failures += 1
                continue
            print(f"VERIFY {case}: {trace}")
            result = subprocess.run(
                [sys.executable, str(verifier), target, str(trace)],
                check=False,
            )
            if result.returncode:
                print(f"FAIL {case}: production userspace verifier returned {result.returncode}")
                failures += 1
            else:
                print(f"PASS {case}")
    if failures:
        print(f"PRODUCTION ACCEPTANCE FAIL: {failures} of 6 cases failed or were missing")
        return 1
    print("PRODUCTION ACCEPTANCE PASS: all six target/firmware cases verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
