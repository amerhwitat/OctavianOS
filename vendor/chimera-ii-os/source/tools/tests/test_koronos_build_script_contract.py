#!/usr/bin/env python3
"""Source contract for Koronos kernel build separation and fail-closed init packaging."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    build_path = ROOT / "kernel/build-koronos.sh"
    builder_path = ROOT / "tools/build-production-init-elfs.sh"
    if not build_path.is_file():
        print("KORONOS BUILD CONTRACT FAIL: kernel build script missing", file=sys.stderr)
        return 1
    if not builder_path.is_file():
        print("KORONOS BUILD CONTRACT FAIL: production init builder missing", file=sys.stderr)
        return 1
    build = build_path.read_text(encoding="utf-8")
    builder = builder_path.read_text(encoding="utf-8")
    required = (
        "test_validate_native_init_elf.py",
        "test_native_init_packaging_contract.py",
        "test_native_init_launch_gate.py",
        "test_production_closeout_daps.py",
        "test_target_init_payload_binding.py",
        "kernel/core/process_loader.cpp",
        "kernel/core/target_launch.cpp",
        "koronos.elf",
    )
    for token in required:
        if token not in build:
            print(f"KORONOS BUILD CONTRACT FAIL: required build/test token missing: {token}", file=sys.stderr)
            return 1
    for target in ("live", "installer", "recovery"):
        if f"build_one {target} " not in builder:
            print(f"KORONOS BUILD CONTRACT FAIL: production init builder omits target={target}", file=sys.stderr)
            return 1
    if "NATIVE INIT BLOCKED:" not in (ROOT / "kernel/userspace/native_init.c").read_text(encoding="utf-8"):
        print("KORONOS BUILD CONTRACT FAIL: native init must fail closed while services are unavailable", file=sys.stderr)
        return 1
    print("KORONOS BUILD CONTRACT PASS: kernel, target init packaging, and fail-closed readiness policy are wired")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
