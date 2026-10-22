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
        # The kernel parses the marker components and the probe constructs the
        # complete target/PID line; don't require an obsolete logging idiom.
        self.assertIn('"USERSPACE READY: target="', launch)
        self.assertIn('" init_pid="', launch)
        self.assertIn('parse_target_pid_line(bytes,length,"USERSPACE READY: target="," init_pid=",target,pid)', launch)
        self.assertIn('"USERSPACE READY: target=" CHIMERA_TARGET_NAME " init_pid="', probe)
        self.assertNotIn('const char *a="USERSPACE READY: ";', launch)
        self.assertNotIn('"USERSPACE READY: " CHIMERA_TARGET_NAME " init pid="', probe)

    def test_ci_regex_and_timeout_negative_assertion_match_contract(self):
        workflow = ACCEPTANCE.read_text(encoding="utf-8")
        self.assertIn('USERSPACE READY: target=${TARGET} init_pid=[1-9][0-9]*', workflow)
        # Negative timeout probe rejects the full canonical marker, including
        # the required nonzero PID; it cannot pass on a truncated prefix.
        self.assertIn('! grep -Fq "USERSPACE READY: target=live init_pid=" "$LOG"', workflow)
        self.assertNotIn('USERSPACE READY: ${TARGET} init pid=', workflow)

    def test_production_verifier_uses_same_target_and_pid_names(self):
        verifier = VERIFY.read_text(encoding="utf-8")
        self.assertIn('USER INIT SYSCALL: target=(live|installer|recovery) init_pid=([1-9][0-9]*)', verifier)
        self.assertIn('USERSPACE READY: target=(live|installer|recovery) init_pid=([1-9][0-9]*)', verifier)
        self.assertIn("marker.group(2) == entry.group(2)", verifier)


if __name__ == "__main__":
    unittest.main()
