"""Regression: OctavianOS DAPS must inspect artifact files, not just JSON claims."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DAPS = ROOT / "tools" / "production-closeout-daps.py"


class ArtifactValidationTests(unittest.TestCase):
    def test_cli_rejects_missing_artifacts_even_when_report_claims_pass(self):
        cases = {}
        for target in ("live", "installer", "recovery"):
            for firmware in ("bios", "uefi"):
                case_id = f"{target}-{firmware}"
                case = {
                    "status": "PASS",
                    "production_iso": "missing-production.iso",
                    "iso_sha256": "a" * 64,
                    "raw_trace": f"traces/{case_id}.log",
                    "cpl3_syscall_ack": True,
                    "process_visible_rootfs": True,
                    "display_mode_verified": True,
                    "display_mode": "1024x768",
                    "display_mode_evidence": "missing-display.log",
                    "rootfs_file_syscalls_verified": True,
                    "rootfs_file_syscalls_evidence": "missing-vfs.log",
                    "syscall_pid": 42,
                    "readiness_pid": 42,
                }
                if target in ("live", "recovery"):
                    case["tmpfs_mutation_verified"] = True
                    case["tmpfs_mutation_evidence"] = "missing-tmpfs.log"
                cases[case_id] = case
        report = {
            "production_iso_sha256": "a" * 64,
            "cases": cases,
            "display": {
                "status": "PASS", "framebuffer_detected_verified": True,
                "highest_supported_mode_verified": True,
                "fallback_1024x768_verified": True, "fallback_640x480_verified": True,
                "aurora_compositor_handoff_verified": True, "selected_mode": "1024x768",
                "evidence": "missing-display.log",
            },
            "aurora_handoff": {"status": "PASS", "evidence": "missing-aurora.log"},
            "installer_persistence": {
                "status": "PASS", "write_verified": True, "cold_reboot_verified": True,
                "readback_verified": True, "evidence": "missing-installer.log",
            },
            "recovery_repair": {
                "status": "PASS", "repair_verified": True,
                "postcondition_verified": True, "evidence": "missing-recovery.log",
            },
            "smp": {
                "status": "PASS", "ap_startup_verified": True,
                "overlapping_execution_verified": True, "cpu_ids": [0, 1],
                "evidence": "missing-smp.log",
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            evidence = Path(tmp) / "evidence.json"
            evidence.write_text(json.dumps(report), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(DAPS), str(evidence)],
                text=True, capture_output=True, check=False,
            )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("artifact file does not exist", result.stdout)

        # A case-level digest is not enough: every case must bind to the
        # single declared production ISO identity used for the closeout.
        report.pop("production_iso_sha256")
        with tempfile.TemporaryDirectory() as tmp:
            evidence = Path(tmp) / "evidence.json"
            evidence.write_text(json.dumps(report), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(DAPS), str(evidence)],
                text=True, capture_output=True, check=False,
            )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("production_iso_sha256 must be a required", result.stdout)
        self.assertIn("cannot bind case ISO to a missing/invalid top-level", result.stdout)


if __name__ == "__main__":
    unittest.main()
