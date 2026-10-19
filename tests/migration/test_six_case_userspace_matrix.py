"""Tests for the six-case production matrix's provenance and independence checks."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("verify-six-case-userspace-matrix.py")
TARGETS = ("live", "installer", "recovery")
FIRMWARES = ("bios", "uefi")
KERNEL = "[KRN ] KORONOS READY\n"


def trace_text(target, firmware, pid):
    return (
        f"QEMU BOOT PROVENANCE: target={target} firmware={firmware}\n"
        + KERNEL
        + f"USER INIT SYSCALL: target={target} init_pid={pid}\n"
        + f"USERSPACE READY: target={target} init_pid={pid}\n"
    )


class SixCaseMatrixTests(unittest.TestCase):
    def run_matrix(self, root):
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(root)],
            capture_output=True,
            text=True,
        )

    def test_accepts_six_distinct_firmware_attested_handoffs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for i, target in enumerate(TARGETS):
                for j, firmware in enumerate(FIRMWARES):
                    (root / f"{target}-{firmware}.log").write_text(
                        trace_text(target, firmware, i * 2 + j + 1),
                        encoding="utf-8",
                    )
            result = self.run_matrix(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("all six independent target/firmware cases verified", result.stdout)

    def test_rejects_wrong_firmware_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for target in TARGETS:
                for firmware in FIRMWARES:
                    provenance_firmware = "uefi" if target == "live" and firmware == "bios" else firmware
                    (root / f"{target}-{firmware}.log").write_text(
                        trace_text(target, provenance_firmware, 1),
                        encoding="utf-8",
                    )
            result = self.run_matrix(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("expected harness provenance line", result.stdout)

    def test_rejects_byte_identical_copied_trace(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for target in TARGETS:
                for firmware in FIRMWARES:
                    (root / f"{target}-{firmware}.log").write_text(
                        trace_text(target, firmware, 1),
                        encoding="utf-8",
                    )
            source = root / "live-bios.log"
            (root / "live-uefi.log").write_bytes(source.read_bytes())
            result = self.run_matrix(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("byte-identical", result.stdout)


if __name__ == "__main__":
    unittest.main()
