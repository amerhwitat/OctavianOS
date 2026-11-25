"""Regression tests for fail-closed userspace acceptance and prerelease publication."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/native-koronos-build.yml"

class UserspaceReleaseWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_userspace_gate_is_a_separate_job_after_iso_build(self):
        self.assertIn("  verify-userspace-handoff:", self.text)
        self.assertIn("needs: build-koronos", self.text)
        self.assertIn("python3 tests/boot/verify-userspace-handoff.py live trace/full-iso-debugcon.log", self.text)
        self.assertIn("python3 tests/boot/verify-userspace-handoff.py installer trace/installer-debugcon.log", self.text)
        self.assertIn("python3 tests/boot/verify-userspace-handoff.py recovery trace/recovery-debugcon.log", self.text)

    def test_release_gate_stays_blocked_without_production_acceptance(self):
        section = self.text.split("  publish-native-iso:", 1)[1]
        self.assertIn("needs: [build-koronos, verify-userspace-handoff]", section)
        self.assertIn("needs.verify-userspace-handoff.outputs.production_runtime_accepted == 'true'", section)
        self.assertIn("Published only after Live, Installer, and Recovery userspace handoff gates pass.", section)

    def test_trace_evidence_job_cannot_authorize_release(self):
        section = self.text.split("  verify-userspace-handoff:", 1)[1]
        section = section.split("  publish-native-iso:", 1)[0]
        self.assertIn("production acceptance Outstanding", section)
        self.assertIn('echo "production_runtime_accepted=false" >> "$GITHUB_OUTPUT"', section)
        self.assertIn("| Production release | BLOCKED |", section)

    def test_build_uploads_each_real_target_trace(self):
        section = self.text.split("      - name: Upload Live, Installer, and Recovery QEMU traces", 1)[1]
        section = section.split("      - name:", 1)[0]
        for trace in ("full-iso-debugcon.log", "installer-debugcon.log", "recovery-debugcon.log"):
            self.assertIn(trace, section)

if __name__ == "__main__":
    unittest.main()
