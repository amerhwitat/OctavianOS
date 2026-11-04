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
        self.assertIn("python3 tests/migration/verify-userspace-handoff.py live trace/full-iso-debugcon.log", self.text)
        self.assertIn("python3 tests/migration/verify-userspace-handoff.py installer trace/installer-debugcon.log", self.text)
        self.assertIn("python3 tests/migration/verify-userspace-handoff.py recovery trace/recovery-debugcon.log", self.text)

    def test_release_depends_on_all_three_userspace_gates(self):
        section = self.text.split("  publish-native-iso:", 1)[1]
        self.assertIn("needs: [build-koronos, verify-userspace-handoff, verify-six-case-matrix]", section)
        self.assertIn("needs.verify-six-case-matrix.outputs.accepted == 'true'", section)
        self.assertIn("if: github.event_name == 'push' && github.ref == 'refs/heads/main'", section)
        self.assertIn("Published only after Live, Installer, and Recovery userspace handoff gates pass.", section)

    def test_six_case_gate_requires_one_immutable_iso_and_fails_closed(self):
        self.assertIn("  verify-six-case-matrix:", self.text)
        self.assertIn("verify-six-case-matrix.py", self.text)
        self.assertIn("six-case-evidence/report.json", self.text)
        self.assertIn("Current per-target repacked probe ISOs and test init ELFs are not production evidence.", self.text)

    def test_alternate_release_artifact_workflow_cannot_bypass_six_case_gate(self):
        alternate = (ROOT / ".github/workflows/release-artifacts.yml").read_text(encoding="utf-8")
        section = alternate.split("  publish:", 1)[1]
        self.assertIn("verify-six-case-matrix.outputs.accepted == 'true'", section)
        self.assertIn("needs: [container, iso, verify-six-case-matrix]", section)
        self.assertIn("verify-six-case-matrix.py", alternate)

    def test_build_uploads_each_real_target_trace(self):
        section = self.text.split("      - name: Upload Live, Installer, and Recovery QEMU traces", 1)[1]
        section = section.split("      - name:", 1)[0]
        for trace in ("full-iso-debugcon.log", "installer-debugcon.log", "recovery-debugcon.log"):
            self.assertIn(trace, section)

if __name__ == "__main__":
    unittest.main()
