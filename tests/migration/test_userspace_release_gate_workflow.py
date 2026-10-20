"""Regression tests for fail-closed production userspace acceptance and publication."""
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
        self.assertIn('for target in live installer recovery; do', self.text)
        self.assertIn('for firmware in bios uefi; do', self.text)
        for target in ("live", "installer", "recovery"):
            for firmware in ("bios", "uefi"):
                self.assertIn(
                    f'python3 tests/migration/verify-userspace-handoff.py "$target" "trace/$target-$firmware-debugcon.log"',
                    self.text,
                )

    def test_release_depends_on_all_userspace_cases(self):
        section = self.text.split("  publish-native-iso:", 1)[1]
        self.assertIn("needs: [build-koronos, verify-userspace-handoff]", section)
        self.assertIn("if: github.event_name == 'push' && github.ref == 'refs/heads/main'", section)
        self.assertIn("Published only after Live, Installer, and Recovery userspace handoff gates pass.", section)

    def test_build_uploads_six_distinct_target_firmware_traces(self):
        section = self.text.split(
            "      - name: Upload Live, Installer, and Recovery QEMU traces", 1
        )[1].split("      - name:", 1)[0]
        for target in ("live", "installer", "recovery"):
            for firmware in ("bios", "uefi"):
                self.assertIn(f"{target}-{firmware}-debugcon.log", section)

    def test_production_gate_is_not_the_ring3_probe_workflow(self):
        probe_workflow = (ROOT / ".github/workflows/koronos-userspace-acceptance.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("not production acceptance", probe_workflow)
        self.assertIn("production payload acceptance remains separate", probe_workflow)
        self.assertIn("native-init", self.text.lower() if "native-init" in self.text.lower() else "init")


if __name__ == "__main__":
    unittest.main()
