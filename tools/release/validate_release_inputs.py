#!/usr/bin/env python3
"""Validate real staged ISO inputs before any release can be published."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import struct
import sys

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="staged ISO root directory")
    parser.add_argument("--contract", default="boot/iso/target-payload-contract.json")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    contract_path = Path(args.contract)
    if not contract_path.is_absolute():
        contract_path = Path(__file__).resolve().parents[2] / contract_path
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for target, details in contract["targets"].items():
        for item in details.get("required", []):
            path = root / item.lstrip("/")
            if not path.is_file() or path.stat().st_size == 0:
                errors.append(f"{target}: required payload missing/empty: {item}")
    kernel_rel = contract["kernel"]["path"].lstrip("/")
    kernel = root / kernel_rel
    if not kernel.is_file() or kernel.stat().st_size == 0:
        errors.append(f"kernel: required ELF missing/empty: /{kernel_rel}")
    else:
        data = kernel.read_bytes()
        if data[:4] != b"\x7fELF":
            errors.append("kernel: file is not ELF")
        elif len(data) < 64 or data[4] != 2 or data[5] != 1:
            errors.append("kernel: expected 64-bit little-endian ELF")
        elif struct.unpack_from("<H", data, 18)[0] != 62:
            errors.append("kernel: expected x86_64 ELF machine type")
        if b"\xd6\x50\x52\xe8" not in data[:32768]:
            # Multiboot2 magic is 0xE85250D6, little-endian bytes d6 50 52 e8.
            errors.append("kernel: Multiboot2 header magic not found in first 32 KiB")
    if errors:
        print("RELEASE INPUT VALIDATION FAILED", file=sys.stderr)
        for error in errors:
            print(f" - {error}", file=sys.stderr)
        return 2
    print("Release inputs validated; this proves staging integrity only, not successful boot.")
    print(json.dumps({"kernel_bytes": kernel.stat().st_size, "targets": sorted(contract["targets"])}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
