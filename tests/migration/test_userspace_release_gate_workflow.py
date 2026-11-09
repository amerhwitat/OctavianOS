"""Regression tests for fail-closed userspace acceptance and prerelease publication."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/native-koronos-build.yml"


class UserspaceReleaseWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_userspace_gate_is_separate_and_checks_each_target_probe(self):
        self.assertIn("  verify-userspace-handoff:", self.text)
        section = self.text.split("  verify-userspace-handoff:", 1)[1]
        section = section.split("\n  production-runtime-acceptance:", 1)[0]
        self.assertIn("needs: build-koronos", section)
        self.assertIn("python3 tests/migration/verify-userspace-handoff.py live trace/live-probe-debugcon.log", section)
        self.assertIn("python3 tests/migration/verify-userspace-handoff.py installer trace/installer-debugcon.log", section)
        self.assertIn("python3 tests/migration/verify-userspace-handoff.py recovery trace/recovery-debugcon.log", section)

    def test_production_release_gate_and_publication_are_fail_closed(self):
        runtime = self.text.split("  production-runtime-acceptance:", 1)[1].split("\n  publish-native-iso:", 1)[0]
        self.assertIn("needs: [build-koronos, verify-userspace-handoff]", runtime)
        self.assertIn("if: github.event_name == 'push' && github.ref == 'refs/heads/main'", runtime)
        self.assertIn("verify-production-runtime-acceptance.py", runtime)

        publish = self.text.split("  publish-native-iso:", 1)[1]
        self.assertIn("needs: [build-koronos, verify-userspace-handoff, production-runtime-acceptance]", publish)
        self.assertIn("if: github.event_name == 'push' && github.ref == 'refs/heads/main'", publish)
        self.assertIn("sha256sum -c output.iso.sha256", publish)

    def test_build_uploads_all_target_specific_probe_traces(self):
        section = self.text.split("      - name: Upload production ISO and isolated ring-3 probe traces", 1)[1]
        section = section.split("      - name:", 1)[0]
        for trace in ("live-probe-debugcon.log", "full-iso-debugcon.log",
                      "installer-debugcon.log", "recovery-debugcon.log"):
            self.assertIn(trace, section)


if __name__ == "__main__":
    unittest.main()
