#!/usr/bin/env python3
"""Fail-closed validator for target-specific x86-64 native init ELF files."""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

EHDR = struct.Struct("<16sHHIQQQIHHHHHH")
PHDR = struct.Struct("<IIQQQQQQ")
MAX_BYTES = 64 * 1024 * 1024
TARGET_PATHS = {
    "live": Path("boot/live/user-init-live.elf"),
    "installer": Path("boot/installer/user-init-installer.elf"),
    "recovery": Path("boot/recovery/user-init-recovery.elf"),
}

def inspect(path: Path, target: str) -> dict:
    data = path.read_bytes()
    if not data or len(data) > MAX_BYTES or len(data) < EHDR.size:
        raise ValueError(f"{target}: ELF file size is outside valid bounds")
    h = EHDR.unpack_from(data)
    ident, etype, machine, version, entry, phoff, _shoff, _flags, ehsize, phentsize, phnum, *_ = h
    if ident[:4] != b"\x7fELF" or ident[4:7] != bytes((2, 1, 1)):
        raise ValueError(f"{target}: expected ELF64 little-endian version 1")
    if etype != 2 or machine != 62 or version != 1:
        raise ValueError(f"{target}: expected x86-64 ET_EXEC")
    if ehsize != EHDR.size or phentsize != PHDR.size or not 1 <= phnum <= 128:
        raise ValueError(f"{target}: invalid ELF/program-header dimensions")
    if phoff > len(data) or phnum * phentsize > len(data) - phoff:
        raise ValueError(f"{target}: program-header table exceeds file bounds")
    loads = []
    for i in range(phnum):
        p_type, flags, offset, vaddr, _paddr, filesz, memsz, align = PHDR.unpack_from(data, phoff + i * phentsize)
        if p_type != 1:
            continue
        if filesz > memsz or offset > len(data) or filesz > len(data) - offset:
            raise ValueError(f"{target}: invalid PT_LOAD file/memory bounds")
        if memsz == 0 or vaddr < 0x10000 or vaddr + memsz > 0x0000800000000000 or vaddr + memsz < vaddr:
            raise ValueError(f"{target}: invalid/noncanonical PT_LOAD virtual range")
        if flags & 2 and flags & 1:
            raise ValueError(f"{target}: writable+executable PT_LOAD violates W^X")
        if align > 1 and ((align & (align - 1)) or vaddr % align != offset % align):
            raise ValueError(f"{target}: invalid PT_LOAD alignment")
        loads.append((vaddr, vaddr + memsz, flags))
    ordered = sorted((start, end) for start, end, _ in loads)
    if any(ordered[i][0] < ordered[i - 1][1] for i in range(1, len(ordered))):
        raise ValueError(f"{target}: overlapping PT_LOAD virtual ranges")
    if not loads or not any((flags & 1) and start <= entry < end for start, end, flags in loads):
        raise ValueError(f"{target}: entry point is not inside executable PT_LOAD")
    return {"target": target, "path": "/" + TARGET_PATHS[target].as_posix(),
            "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "entry": f"0x{entry:x}", "load_segments": len(loads)}

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, choices=sorted(TARGET_PATHS))
    parser.add_argument("elf", type=Path)
    args = parser.parse_args()
    try:
        record = inspect(args.elf, args.target)
    except (OSError, ValueError, struct.error) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: " + json.dumps(record, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
