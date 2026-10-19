#!/usr/bin/env python3
"""Strict structural validation for production Koronos user-init ELF64 payloads.

This checks ELF admission preconditions only; it does not claim that the process
runs, that the target works, or that userspace is ready. Runtime acceptance is
a separate gate.
"""
from __future__ import annotations
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
PAYLOAD_DIR = ROOT / "vendor/chimera-ii-os/source/build/koronos/userspace"
TARGETS = ("live", "installer", "recovery")
ELF_HEADER = struct.Struct("<16sHHIQQQIHHHHHH")
PROGRAM_HEADER = struct.Struct("<IIQQQQQQ")
PT_LOAD = 1
PF_X = 1
PF_W = 2
EM_X86_64 = 62
ET_EXEC = 2
MAX_FILE_SIZE = 64 * 1024 * 1024
MAX_PROGRAM_HEADERS = 128


def validate(path: pathlib.Path) -> list[str]:
    errors: list[str] = []
    try:
        data = path.read_bytes()
    except OSError as exc:
        return [f"{path}: cannot read payload: {exc}"]
    if not data or len(data) > MAX_FILE_SIZE:
        return [f"{path}: empty or oversized ELF ({len(data)} bytes)"]
    if len(data) < ELF_HEADER.size:
        return [f"{path}: truncated ELF header"]
    fields = ELF_HEADER.unpack_from(data)
    ident, e_type, e_machine, _version, entry, phoff, _shoff, _flags, ehsize, phentsize, phnum, *_ = fields
    if ident[:4] != b"\x7fELF" or ident[4] != 2 or ident[5] != 1 or ident[6] != 1:
        errors.append(f"{path}: expected ELF64, little-endian, current-version image")
    if e_type != ET_EXEC:
        errors.append(f"{path}: expected ET_EXEC, got e_type={e_type}")
    if e_machine != EM_X86_64:
        errors.append(f"{path}: expected x86-64 (EM_X86_64=62), got {e_machine}")
    if ehsize < ELF_HEADER.size or phentsize < PROGRAM_HEADER.size:
        errors.append(f"{path}: invalid ELF/program-header entry size")
    if phnum == 0 or phnum > MAX_PROGRAM_HEADERS:
        errors.append(f"{path}: invalid program-header count {phnum}")
    table_end = phoff + phentsize * phnum
    if phoff < ehsize or table_end < phoff or table_end > len(data):
        errors.append(f"{path}: program-header table out of file bounds")
        return errors
    executable_ranges: list[tuple[int, int]] = []
    load_count = 0
    for index in range(phnum):
        off = phoff + index * phentsize
        p_type, p_flags, p_offset, p_vaddr, _paddr, p_filesz, p_memsz, p_align = PROGRAM_HEADER.unpack_from(data, off)
        if p_type != PT_LOAD:
            continue
        load_count += 1
        if p_filesz > p_memsz:
            errors.append(f"{path}: PT_LOAD[{index}] filesz exceeds memsz")
        end = p_offset + p_filesz
        if end < p_offset or end > len(data):
            errors.append(f"{path}: PT_LOAD[{index}] file range is out of bounds")
        if p_align not in (0, 1) and p_align & (p_align - 1):
            errors.append(f"{path}: PT_LOAD[{index}] alignment is not a power of two")
        if p_flags & PF_W and p_flags & PF_X:
            errors.append(f"{path}: PT_LOAD[{index}] violates W^X (writable and executable)")
        if p_flags & PF_X:
            executable_ranges.append((p_vaddr, p_vaddr + p_memsz))
    if load_count == 0:
        errors.append(f"{path}: no PT_LOAD segments")
    if not any(start <= entry < end for start, end in executable_ranges):
        errors.append(f"{path}: entry point 0x{entry:x} is not inside an executable PT_LOAD segment")
    if not errors:
        print(f"ELF STRUCTURE PASS: {path.name} ({len(data)} bytes, entry=0x{entry:x}, PT_LOAD={load_count})")
    return errors


def main() -> int:
    errors: list[str] = []
    for target in TARGETS:
        path = PAYLOAD_DIR / f"{target}-init.elf"
        errors.extend(validate(path))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print("NOT ACCEPTED: ELF structure validation is not a substitute for runtime acceptance.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
