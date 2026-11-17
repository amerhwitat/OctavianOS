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
        for target in ("live", "installer", "recovery"):
            module = (
                f"module2 /boot/target-init-{target}.elf "
                f"chimera-user-init-elf target={target} firmware=$grub_platform"
            )
            self.assertIn(module, self.acceptance_workflow)

    def test_acceptance_workflow_triggers_for_boot_graph_contract_changes(self):
        pull_request_start = self.acceptance_workflow.index("  pull_request:")
        push_start = self.acceptance_workflow.index("  push:", pull_request_start)
        permissions_start = self.acceptance_workflow.index("permissions:", push_start)
        pull_request_paths = self.acceptance_workflow[pull_request_start:push_start]
        push_paths = self.acceptance_workflow[push_start:permissions_start]
        self.assertIn("- 'tests/boot/**'", pull_request_paths)
        self.assertIn("- 'tests/boot/**'", push_paths)

    def test_workflow_requires_userspace_originated_evidence(self):
        self.assertIn("verify-userspace-handoff.py", self.workflow)
        self.assertIn("for target in live installer recovery; do", self.workflow)
        self.assertIn("for firmware in bios uefi; do", self.workflow)
        self.assertIn('trace="six-case-evidence/$target/$firmware/debugcon.log"', self.workflow)


if __name__ == "__main__":
    unittest.main()
