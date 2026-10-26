#!/usr/bin/env python3
import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "koronos" / "validate_elf.py"
SPEC = importlib.util.spec_from_file_location("koronos_validate_elf", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
EHDR, PHDR = MODULE.ELF_HEADER, MODULE.PROGRAM_HEADER


def make_elf(*, machine=62, e_type=2, entry=0x100000, flags=5, p_filesz=4, p_memsz=4):
    ident = b"\x7fELF" + bytes([2, 1, 1]) + bytes(9)
    phoff, data_offset = EHDR.size, 0x100
    header = EHDR.pack(ident, e_type, machine, 1, entry, phoff, 0, 0,
                       EHDR.size, PHDR.size, 1, 0, 0, 0)
    program = PHDR.pack(1, flags, data_offset, 0x100000, 0,
                        p_filesz, p_memsz, 0x100)
    return header + program + bytes(data_offset - len(header) - len(program)) + b"CODE"


class KoronosElfValidatorTests(unittest.TestCase):
    def validate_bytes(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "kernel.elf"
            path.write_bytes(data)
            return MODULE.validate(path)

    def test_accepts_valid_x86_64_executable(self):
        self.assertIn("ELF validation PASS", self.validate_bytes(make_elf()))

    def test_rejects_wrong_machine(self):
        with self.assertRaisesRegex(ValueError, "EM_X86_64"):
            self.validate_bytes(make_elf(machine=183))

    def test_rejects_non_executable_elf_type(self):
        with self.assertRaisesRegex(ValueError, "ET_EXEC"):
            self.validate_bytes(make_elf(e_type=3))

    def test_rejects_entry_outside_executable_segment(self):
        with self.assertRaisesRegex(ValueError, "entry point"):
            self.validate_bytes(make_elf(entry=0x200000))

    def test_rejects_writable_executable_segment(self):
        with self.assertRaisesRegex(ValueError, "W\\^X"):
            self.validate_bytes(make_elf(flags=7))

    def test_rejects_file_size_larger_than_memory_size(self):
        with self.assertRaisesRegex(ValueError, "file size exceeds memory size"):
            self.validate_bytes(make_elf(p_filesz=8, p_memsz=4))

    def test_rejects_truncated_program_header_table(self):
        data = bytearray(make_elf())
        struct.pack_into("<Q", data, 32, len(data) - 4)
        with self.assertRaisesRegex(ValueError, "program-header table"):
            self.validate_bytes(bytes(data))


if __name__ == "__main__":
    unittest.main()
