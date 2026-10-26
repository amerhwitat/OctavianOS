#!/usr/bin/env python3
"""Guard the production closeout contract against fabricated readiness/DAPS evidence."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    init_path = ROOT / "kernel/userspace/native_init.c"
    launch_path = ROOT / "kernel/core/target_launch.cpp"
    if not init_path.is_file() or not launch_path.is_file():
        print("PRODUCTION CLOSEOUT FAIL: native init or target launcher source missing", file=sys.stderr)
        return 1
    init = init_path.read_text(encoding="utf-8")
    launch = launch_path.read_text(encoding="utf-8")
    if "NATIVE INIT BLOCKED:" not in init or "call1(1, code)" not in init or "stop_after_exit_failure(78)" not in init:
        print("PRODUCTION CLOSEOUT FAIL: unavailable services must cause explicit nonzero exit", file=sys.stderr)
        return 1
    if "USERSPACE READY:" in init or "AURORA READY" in init:
        print("PRODUCTION CLOSEOUT FAIL: native init must not synthesize desktop/readiness markers", file=sys.stderr)
        return 1
    for token in (
        "koronos_target_note_user_syscall",
        "koronos_target_note_user_write",
        "target_marker(bytes,length",
        "userspace init exited before its target-specific USERSPACE READY handshake",
    ):
        if token not in launch:
            print(f"PRODUCTION CLOSEOUT FAIL: launch evidence contract missing: {token}", file=sys.stderr)
            return 1
    if "PRODUCTION DAPS: PASS" in launch or "PRODUCTION DAPS: PASS" in init:
        print("PRODUCTION CLOSEOUT FAIL: kernel/init must not author a DAPS pass result", file=sys.stderr)
        return 1
    print("PRODUCTION CLOSEOUT PASS: unavailable services remain blocked; readiness/DAPS are not fabricated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
