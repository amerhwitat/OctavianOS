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
        self.assertIn("for target in live installer recovery; do", self.text)
        self.assertIn("for firmware in bios uefi; do", self.text)
        self.assertIn('log="trace/acceptance-$target-$firmware/debugcon.log"', self.text)
        self.assertIn('python3 tests/migration/verify-userspace-handoff.py "$target" "$log" || result=1', self.text)
        self.assertIn("Missing full-ISO target trace: $target/$firmware", self.text)

    def test_release_depends_on_all_three_userspace_gates(self):
        section = self.text.split("  publish-native-iso:", 1)[1]
        self.assertIn("needs: [build-koronos, verify-userspace-handoff]", section)
        self.assertIn("if: github.event_name == 'push' && github.ref == 'refs/heads/main'", section)
        self.assertIn("Published only after Live, Installer, and Recovery userspace handoff gates pass.", section)

    def test_build_uploads_each_real_target_trace(self):
        section = self.text.split("      - name: Upload Live, Installer, and Recovery QEMU traces", 1)[1]
        section = section.split("      - name:", 1)[0]
        for trace in ("full-iso-debugcon.log", "installer-debugcon.log", "recovery-debugcon.log", "acceptance-*/debugcon.log"):
            self.assertIn(trace, section)
        self.assertIn("Capture real target init traces for BIOS and isolated OVMF UEFI", self.text)

if __name__ == "__main__":
    unittest.main()
