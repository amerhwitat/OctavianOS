#!/usr/bin/env python3
"""Fail-closed structural validation for the freestanding Koronos x86-64 ELF."""
from __future__ import annotations
import struct
import sys
from pathlib import Path

ELF_HEADER = struct.Struct("<16sHHIQQQIHHHHHH")
PROGRAM_HEADER = struct.Struct("<IIQQQQQQ")
ELFCLASS64, ELFDATA2LSB, ET_EXEC, EM_X86_64, EV_CURRENT = 2, 1, 2, 62, 1
PT_LOAD, PF_X, PF_W = 1, 1, 2


def validate(path: str | Path) -> str:
    path = Path(path)
    data = path.read_bytes()
    if len(data) < ELF_HEADER.size:
        raise ValueError(f"invalid ELF64 header: file is shorter than {ELF_HEADER.size} bytes")
    (ident, e_type, machine, version, entry, phoff, _shoff, _flags,
     ehsize, phentsize, phnum, _shentsize, _shnum, _shstrndx) = ELF_HEADER.unpack_from(data)
    if ident[:4] != b"\x7fELF" or ident[4] != ELFCLASS64 or ident[5] != ELFDATA2LSB:
        raise ValueError("expected a little-endian ELF64 file")
    if ident[6] != EV_CURRENT or version != EV_CURRENT:
        raise ValueError("unsupported ELF version")
    if e_type != ET_EXEC:
        raise ValueError(f"expected ET_EXEC (2), got e_type={e_type}")
    if machine != EM_X86_64:
        raise ValueError(f"expected EM_X86_64 (62), got e_machine={machine}")
    if ehsize != ELF_HEADER.size:
        raise ValueError(f"invalid ELF header size: {ehsize}")
    if phnum == 0:
        raise ValueError("ELF has no program headers")
    if phentsize != PROGRAM_HEADER.size:
        raise ValueError(f"invalid program-header entry size: {phentsize}")
    if phoff > len(data) or phnum > (len(data) - phoff) // phentsize:
        raise ValueError("program-header table extends beyond the file")
    if entry == 0:
        raise ValueError("ELF entry point is zero")

    executable_loads = []
    load_count = 0
    for index in range(phnum):
        (p_type, p_flags, p_offset, p_vaddr, _paddr, p_filesz,
         p_memsz, p_align) = PROGRAM_HEADER.unpack_from(data, phoff + index * phentsize)
        if p_type != PT_LOAD:
            continue
        load_count += 1
        if p_filesz > p_memsz:
            raise ValueError(f"PT_LOAD[{index}] file size exceeds memory size")
        if p_offset > len(data) or p_filesz > len(data) - p_offset:
            raise ValueError(f"PT_LOAD[{index}] file range extends beyond the ELF")
        if p_vaddr > 0xFFFFFFFFFFFFFFFF - p_memsz:
            raise ValueError(f"PT_LOAD[{index}] virtual-address range overflows")
        if p_align not in (0, 1) and p_align & (p_align - 1):
            raise ValueError(f"PT_LOAD[{index}] alignment is not a power of two")
        if (p_flags & (PF_W | PF_X)) == (PF_W | PF_X):
            raise ValueError(f"PT_LOAD[{index}] violates W^X (writable and executable)")
        if p_flags & PF_X and p_memsz and p_vaddr <= entry < p_vaddr + p_memsz:
            executable_loads.append(index)
    if load_count == 0:
        raise ValueError("ELF has no PT_LOAD segments")
    if not executable_loads:
        raise ValueError("entry point is not inside an executable PT_LOAD segment")
    return (f"ELF validation PASS: {path}: ELF64 little-endian ET_EXEC "
            f"EM_X86_64 PT_LOAD={load_count} entry=0x{entry:x} "
            f"executable_entry_segment={executable_loads[0]}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_elf.py <file>")
    try:
        print(validate(sys.argv[1]))
    except (OSError, ValueError) as error:
        raise SystemExit(f"ELF validation FAIL: {error}") from error
