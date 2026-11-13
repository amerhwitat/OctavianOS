import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("verify-userspace-handoff.py")
KERNEL = "[KRN ] KORONOS READY\n"
ENTRY = "USER INIT SYSCALL: target={target} init_pid={pid}\n"
READY = "USERSPACE READY: target={target} init_pid={pid}\n"
ACTIVE = "KORONOS PID1 ACTIVE: target={target} init_pid={pid}\n"
EXITED = "[RUN ] Target userspace init emitted its own readiness handshake and exited cleanly\n"


def run(target, trace):
    with tempfile.TemporaryDirectory() as td:
        log = Path(td) / "trace.log"
        log.write_text(trace, encoding="utf-8")
        return subprocess.run([sys.executable, str(SCRIPT), target, str(log)], capture_output=True, text=True)


class UserspaceHandoffVerifierTests(unittest.TestCase):
    def test_kernel_ready_alone_is_not_userspace_ready(self):
        result = run("live", KERNEL)
        self.assertEqual(result.returncode, 1)
        self.assertIn("user-originated init syscall acknowledgement", result.stdout)

    def test_readiness_marker_without_user_entry_ack_is_rejected(self):
        result = run("live", KERNEL + READY.format(target="live", pid=1))
        self.assertEqual(result.returncode, 1)
        self.assertIn("user-originated init syscall acknowledgement", result.stdout)

    def test_rejects_readiness_without_persistent_pid1_evidence(self):
        trace = KERNEL + ENTRY.format(target="live", pid=1) + READY.format(target="live", pid=1)
        result = run("live", trace)
        self.assertEqual(result.returncode, 1)
        self.assertIn("persistent PID 1 active marker", result.stdout)

    def test_rejects_init_that_exits_after_readiness(self):
        trace = (KERNEL + ENTRY.format(target="live", pid=1)
                 + READY.format(target="live", pid=1) + ACTIVE.format(target="live", pid=1) + EXITED)
        result = run("live", trace)
        self.assertEqual(result.returncode, 1)
        self.assertIn("PID 1 terminated or was aborted", result.stdout)

    def test_requires_matching_target(self):
        trace = (KERNEL + ENTRY.format(target="live", pid=1)
                 + READY.format(target="live", pid=1) + ACTIVE.format(target="live", pid=1))
        result = run("installer", trace)
        self.assertEqual(result.returncode, 1)
        self.assertIn("persistent PID1-active markers", result.stdout)

    def test_requires_same_pid_for_entry_ready_and_active(self):
        trace = (KERNEL + ENTRY.format(target="live", pid=1)
                 + READY.format(target="live", pid=1) + ACTIVE.format(target="live", pid=2))
        self.assertEqual(run("live", trace).returncode, 1)

    def test_requires_ordered_markers(self):
        trace = (ACTIVE.format(target="live", pid=1) + READY.format(target="live", pid=1)
                 + ENTRY.format(target="live", pid=1) + KERNEL)
        self.assertEqual(run("live", trace).returncode, 1)

    def test_accepts_persistent_live_pid1(self):
        trace = (KERNEL + ENTRY.format(target="live", pid=1)
                 + READY.format(target="live", pid=1) + ACTIVE.format(target="live", pid=1))
        result = run("live", trace)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("persistent PID 1", result.stdout)

    def test_accepts_persistent_recovery_pid1_with_nonzero_pid(self):
        trace = (KERNEL + ENTRY.format(target="recovery", pid=2)
                 + READY.format(target="recovery", pid=2) + ACTIVE.format(target="recovery", pid=2))
        self.assertEqual(run("recovery", trace).returncode, 0)

    def test_rejects_zero_or_mismatched_pid(self):
        self.assertEqual(run("recovery", KERNEL + ENTRY.format(target="live", pid=1) + READY.format(target="live", pid=1) + ACTIVE.format(target="live", pid=1)).returncode, 1)
        self.assertEqual(run("recovery", KERNEL + ENTRY.format(target="recovery", pid=0) + READY.format(target="recovery", pid=0) + ACTIVE.format(target="recovery", pid=0)).returncode, 1)


if __name__ == "__main__":
    unittest.main()
