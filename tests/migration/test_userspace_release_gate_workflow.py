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
        self.assertIn("python3 tests/migration/verify-userspace-handoff.py live trace/live-debugcon.log", self.text)
        self.assertIn("python3 tests/migration/verify-userspace-handoff.py installer trace/installer-debugcon.log", self.text)
        self.assertIn("python3 tests/migration/verify-userspace-handoff.py recovery trace/recovery-debugcon.log", self.text)

    def test_release_depends_on_all_three_userspace_gates(self):
        section = self.text.split("  publish-native-iso:", 1)[1]
        self.assertIn("needs: [build-koronos, verify-userspace-handoff]", section)
        self.assertIn("if: github.event_name == 'push' && github.ref == 'refs/heads/main'", section)
        self.assertIn("Published only after Live, Installer, and Recovery userspace handoff gates pass.", section)

    def test_build_uploads_each_real_target_trace(self):
        section = self.text.split("      - name: Upload Live, Installer, and Recovery QEMU traces", 1)[1]
        section = section.split("      - name:", 1)[0]
        for trace in ("full-iso-debugcon.log", "live-debugcon.log", "installer-debugcon.log", "recovery-debugcon.log"):
            self.assertIn(trace, section)

    def test_each_target_qemu_smoke_attaches_native_init_and_ai_modules(self):
        for target in ("live", "installer", "recovery"):
            self.assertIn(f"target-init-{target}.elf chimera-user-init-elf target={target}", self.text)
        self.assertGreaterEqual(self.text.count("module2 /boot/ai/knowledge-db.json ai-knowledge-db"), 3)
        self.assertNotIn("handoff withheld", self.text)

    def test_full_iso_smoke_selects_default_from_long_timeout_menu(self):
        self.assertIn("sendkey ret", self.text)
        self.assertIn("set timeout=300", self.text)

if __name__ == "__main__":
    unittest.main()
