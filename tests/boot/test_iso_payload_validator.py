#!/usr/bin/env python3
"""Tests for the extracted-ISO payload validator using synthetic disposable files."""
from pathlib import Path
import json
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/boot"))
from validate_iso_payloads import ValidationError, validate, MULTIBOOT2_MAGIC  # noqa: E402

CONTRACT = ROOT / "boot/iso/target-payload-contract.json"


def fake_kernel(machine=62, include_multiboot=True):
    data = bytearray(128)
    data[:4] = b"\x7fELF"
    data[4] = 2
    data[5] = 1
    struct.pack_into("<H", data, 18, machine)
    if include_multiboot:
        length = 16
        checksum = (- (MULTIBOOT2_MAGIC + length)) & 0xFFFFFFFF
        struct.pack_into("<IIII", data, 64, MULTIBOOT2_MAGIC, 0, length, checksum)
    return bytes(data)


class IsoPayloadValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        kernel = self.root / "boot/koronos/koronos.elf"
        kernel.parent.mkdir(parents=True)
        kernel.write_bytes(fake_kernel())
        for target in self.contract["targets"].values():
            for absolute in target["required"]:
                path = self.root / absolute.lstrip("/")
                path.parent.mkdir(parents=True, exist_ok=True)
                if absolute.endswith("desktop-sessions.json"):
                    path.write_text((ROOT / "boot/live/desktop-sessions.json").read_text(encoding="utf-8"), encoding="utf-8")
                elif absolute.endswith(".json"):
                    path.write_text("{}", encoding="utf-8")
                else:
                    path.write_bytes(b"synthetic test payload")
        self.contract_path = self.root / "contract.json"
        self.contract_path.write_text(json.dumps(self.contract), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_complete_synthetic_iso_payload_contract_passes(self):
        report = validate(self.root, self.contract_path)
        self.assertEqual(report["status"], "payload-contract-passed")
        self.assertIn("live-aurora", report["targets_checked"])
        self.assertIn("live-marine", report["targets_checked"])
        self.assertTrue(report["kernel"]["multiboot2_header"])

    def test_missing_required_payload_fails(self):
        (self.root / "boot/live/live-manifest.json").unlink()
        with self.assertRaisesRegex(ValidationError, "missing or empty"):
            validate(self.root, self.contract_path)

    def test_wrong_kernel_architecture_fails(self):
        (self.root / "boot/koronos/koronos.elf").write_bytes(fake_kernel(machine=3))
        with self.assertRaisesRegex(ValidationError, "expected x86_64"):
            validate(self.root, self.contract_path)

    def test_missing_multiboot2_header_fails(self):
        (self.root / "boot/koronos/koronos.elf").write_bytes(fake_kernel(include_multiboot=False))
        with self.assertRaisesRegex(ValidationError, "no valid.*Multiboot2"):
            validate(self.root, self.contract_path)

    def test_partial_optional_target_fails(self):
        path = self.root / "boot/retro/retro-manifest.json"
        path.parent.mkdir(parents=True)
        path.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValidationError, "only partially staged"):
            validate(self.root, self.contract_path)


if __name__ == "__main__":
    unittest.main()
