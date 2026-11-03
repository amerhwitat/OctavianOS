"""Ensure the native init readiness ABI is consistent across producer and gates."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
PRODUCER = ROOT / "vendor/chimera-ii-os/source/kernel/tests/user_init_smoke.c"
KERNEL = ROOT / "vendor/chimera-ii-os/source/kernel/core/target_launch.cpp"
VERIFIER = ROOT / "tests/migration/verify-userspace-handoff.py"
WORKFLOW = ROOT / ".github/workflows/koronos-userspace-acceptance.yml"


class KoronosReadinessAbiTests(unittest.TestCase):
    def test_user_probe_emits_verifier_readiness_format(self):
        text = PRODUCER.read_text(encoding="utf-8")
        self.assertIn('USERSPACE READY: target=" CHIMERA_TARGET_NAME " init_pid=', text)

    def test_kernel_parser_consumes_same_readiness_format(self):
        text = KERNEL.read_text(encoding="utf-8")
        self.assertIn('const char *a="USERSPACE READY: target=";', text)
        self.assertIn('const char *b=" init_pid=";', text)

    def test_production_verifier_uses_same_target_and_pid_fields(self):
        text = VERIFIER.read_text(encoding="utf-8")
        self.assertIn(r'USERSPACE READY: target=(live|installer|recovery) init_pid=([1-9][0-9]*)', text)

    def test_candidate_smoke_checks_canonical_readiness_format(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('USERSPACE READY: target=${TARGET} init_pid=[1-9][0-9]*', text)
        self.assertIn('! grep -Fq "USERSPACE READY: target=live" "$LOG"', text)


if __name__ == "__main__":
    unittest.main()
