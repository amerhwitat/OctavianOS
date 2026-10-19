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

    def populate(self, root, wrong_live_bios=False):
        for i, target in enumerate(TARGETS):
            for j, firmware in enumerate(FIRMWARES):
                actual_firmware = (
                    "uefi" if wrong_live_bios and target == "live" and firmware == "bios"
                    else firmware
                )
                (root / f"{target}-{firmware}.log").write_text(
                    trace_text(target, actual_firmware, i * 2 + j + 1),
                    encoding="utf-8",
                )

    def test_kernel_readiness_parser_matches_verifier_contract(self):
        source_root = Path(__file__).parents[2] / "vendor/chimera-ii-os/source/kernel/core/target_launch.cpp"
        verifier = Path(__file__).with_name("verify-userspace-handoff.py").read_text(encoding="utf-8")
        source = source_root.read_text(encoding="utf-8")
        self.assertIn('const char *a="USERSPACE READY: target=";', source)
        self.assertIn('const char *b=" init_pid=";', source)
        self.assertIn('USERSPACE READY: target=(live|installer|recovery) init_pid=([1-9][0-9]*)', verifier)

    def test_accepts_six_distinct_firmware_attested_handoffs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.populate(root)
            result = self.run_matrix(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("all six independent target/firmware cases verified", result.stdout)

    def test_rejects_wrong_firmware_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.populate(root, wrong_live_bios=True)
            result = self.run_matrix(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("expected harness provenance line", result.stdout)

    def test_rejects_byte_identical_copied_trace(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.populate(root)
            (root / "live-uefi.log").write_bytes((root / "live-bios.log").read_bytes())
            result = self.run_matrix(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("byte-identical", result.stdout)


if __name__ == "__main__":
    unittest.main()
