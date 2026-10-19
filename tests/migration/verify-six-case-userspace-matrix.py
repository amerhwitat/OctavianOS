#!/usr/bin/env python3
"""Fail-closed six-case production userspace acceptance matrix.

Each trace must begin with a harness-written provenance line:
QEMU BOOT PROVENANCE: target=<live|installer|recovery> firmware=<bios|uefi>

The harness must write this line only after starting a fresh QEMU instance
with the named target and firmware. Hash uniqueness rejects copied/relabelled
traces. The production verifier remains authoritative for the CPL-3 syscall
and matching-PID readiness handshake. Missing traces are failures, not skips;
missing or ambiguous evidence always fails closed.
"""
from __future__ import annotations

import argparse
import hashlib
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
    seen_hashes: dict[str, str] = {}
    for target in TARGETS:
        for firmware in FIRMWARES:
            trace = args.trace_dir / f"{target}-{firmware}.log"
            case = f"{target.upper()} / {firmware.upper()}"
            if not trace.is_file() or trace.stat().st_size == 0:
                print(f"FAIL {case}: required production trace missing: {trace}")
                failures += 1
                continue

            digest = hashlib.sha256(trace.read_bytes()).hexdigest()
            if digest in seen_hashes:
                print(
                    f"FAIL {case}: trace is byte-identical to {seen_hashes[digest]}; "
                    "each case requires a fresh, independent QEMU boot"
                )
                failures += 1
                continue
            seen_hashes[digest] = case

            expected_provenance = (
                f"QEMU BOOT PROVENANCE: target={target} firmware={firmware}"
            )
            try:
                first_line = trace.open("r", encoding="utf-8", errors="replace").readline().rstrip("\r\n")
            except OSError as exc:
                print(f"FAIL {case}: cannot read trace: {exc}")
                failures += 1
                continue
            if first_line != expected_provenance:
                print(
                    f"FAIL {case}: expected harness provenance line "
                    f"{expected_provenance!r}, got {first_line!r}"
                )
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
    print("PRODUCTION ACCEPTANCE PASS: all six independent target/firmware cases verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
