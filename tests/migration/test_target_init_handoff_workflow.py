#!/usr/bin/env python3
"""Keep each native target QEMU boot wired to its own ring-3 init ELF."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "native-koronos-build.yml"
ACCEPTANCE_WORKFLOW = ROOT / ".github" / "workflows" / "koronos-userspace-acceptance.yml"


class TargetInitHandoffWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.acceptance_workflow = ACCEPTANCE_WORKFLOW.read_text(encoding="utf-8")

    def test_live_installer_and_recovery_load_matching_init_elfs(self):
        for target in ("live", "installer", "recovery"):
            with self.subTest(target=target):
                module = (
                    f"module2 /boot/targets/target-init-{target}.elf "
                    f"chimera-user-init-elf target={target} firmware=$grub_platform"
                )
                self.assertIn(module, self.workflow)
                self.assertIn(f"target-init-{target}.elf", self.workflow)

    def test_acceptance_harness_preserves_grub_firmware_variable(self):
        self.assertIn(
            r"chimera-user-init-elf target=$TARGET firmware=\$grub_platform",
            self.acceptance_workflow,
        )

    def test_workflow_requires_userspace_originated_evidence(self):
        self.assertIn("verify-userspace-handoff.py", self.workflow)
        self.assertIn("verify-userspace-handoff.py live", self.workflow)
        self.assertIn("verify-userspace-handoff.py installer", self.workflow)
        self.assertIn("verify-userspace-handoff.py recovery", self.workflow)


if __name__ == "__main__":
    unittest.main()
