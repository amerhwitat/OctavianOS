"""Regression tests for fail-closed userspace acceptance and prerelease publication."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/native-koronos-build.yml"

class UserspaceReleaseWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_migration_verifier_changes_trigger_native_build_on_pull_requests(self):
        pull_request = self.text.split("  pull_request:", 1)[1].split("\npermissions:", 1)[0]
        self.assertIn("'tests/migration/**'", pull_request)

    def test_userspace_gate_is_a_separate_job_after_iso_build(self):
        self.assertIn("  verify-userspace-handoff:", self.text)
        self.assertIn("needs: build-koronos", self.text)
        self.assertIn("python3 ../../../tests/migration/verify-userspace-handoff.py live trace/full-iso-debugcon.log", self.text)
        self.assertIn("python3 ../../../tests/migration/verify-userspace-handoff.py installer trace/installer-debugcon.log", self.text)
        self.assertIn("python3 ../../../tests/migration/verify-userspace-handoff.py recovery trace/recovery-debugcon.log", self.text)

    def test_release_depends_on_all_three_userspace_gates(self):
        section = self.text.split("  publish-native-iso:", 1)[1]
        self.assertIn("needs: [build-koronos, verify-userspace-handoff]", section)
        self.assertIn("if: github.event_name == 'push' && github.ref == 'refs/heads/main'", section)
        self.assertIn("Published only after Live, Installer, and Recovery userspace handoff gates pass.", section)

    def test_bios_uefi_matrix_requires_persistent_pid1_not_clean_exit(self):
        acceptance = (ROOT / ".github/workflows/koronos-userspace-acceptance.yml").read_text(encoding="utf-8")
        self.assertIn("python3 ../../../tests/migration/verify-userspace-handoff.py \"$TARGET\" \"$LOG\"", acceptance)
        self.assertIn("KORONOS PID1 ACTIVE: target=$TARGET", acceptance)
        self.assertIn("! grep -Fq \"[SYSC] userspace exit syscall received\" \"$LOG\"", acceptance)

    def test_build_uploads_each_real_target_trace(self):
        section = self.text.split("      - name: Upload Live, Installer, and Recovery QEMU traces", 1)[1]
        section = section.split("      - name:", 1)[0]
        for trace in ("full-iso-debugcon.log", "installer-debugcon.log", "recovery-debugcon.log"):
            self.assertIn(trace, section)

if __name__ == "__main__":
    unittest.main()
