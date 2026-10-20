#!/usr/bin/env python3
"""Keep the kernel readiness parser, native probe, and CI verifier on one exact contract."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
LAUNCH = ROOT / "vendor/chimera-ii-os/source/kernel/core/target_launch.cpp"
PROBE = ROOT / "vendor/chimera-ii-os/source/kernel/tests/user_init_smoke.c"
VERIFY = ROOT / "tests/migration/verify-userspace-handoff.py"
ACCEPTANCE = ROOT / ".github/workflows/koronos-userspace-acceptance.yml"


class UserspaceMarkerContractTests(unittest.TestCase):
    def test_kernel_and_probe_emit_same_canonical_marker(self):
        launch = LAUNCH.read_text(encoding="utf-8")
        probe = PROBE.read_text(encoding="utf-8")
        self.assertIn('const char *a="USERSPACE READY: target=";', launch)
        self.assertIn('const char *b=" init_pid=";', launch)
        self.assertIn('"USERSPACE READY: target=" CHIMERA_TARGET_NAME " init_pid="', probe)
        self.assertNotIn('const char *a="USERSPACE READY: ";', launch)
        self.assertNotIn('"USERSPACE READY: " CHIMERA_TARGET_NAME " init pid="', probe)

    def test_ci_regex_and_timeout_negative_assertion_match_contract(self):
        workflow = ACCEPTANCE.read_text(encoding="utf-8")
        self.assertIn('USERSPACE READY: target=${TARGET} init_pid=[1-9][0-9]*', workflow)
        self.assertIn('! grep -Fq "USERSPACE READY: target=live" "$LOG"', workflow)
        self.assertNotIn('USERSPACE READY: ${TARGET} init pid=', workflow)

    def test_production_verifier_uses_same_target_and_pid_names(self):
        verifier = VERIFY.read_text(encoding="utf-8")
        self.assertRegex(verifier, r'USERSPACE READY: target=\(live\|installer\|recovery\) init_pid=')


if __name__ == "__main__":
    unittest.main()
