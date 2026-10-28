import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("verify-userspace-handoff.py")
KERNEL = "[KRN ] KORONOS READY\n"
ENTRY = "USER INIT SYSCALL: target={target} init_pid={pid}\n"
READY = "USERSPACE READY: target={target} init_pid={pid}\n"
TARGET_LAUNCH = Path(__file__).parents[2] / "vendor/chimera-ii-os/source/kernel/core/target_launch.cpp"
SYSCALL_SOURCE = Path(__file__).parents[2] / "vendor/chimera-ii-os/source/kernel/core/syscall.cpp"
PROCESS_HEADER = Path(__file__).parents[2] / "vendor/chimera-ii-os/source/kernel/include/chimera/process.h"
PROCESS_SOURCE = Path(__file__).parents[2] / "vendor/chimera-ii-os/source/kernel/core/process.cpp"
USER_INIT_SMOKE = Path(__file__).parents[2] / "vendor/chimera-ii-os/source/kernel/tests/user_init_smoke.c"
ACCEPTANCE_WORKFLOW = Path(__file__).parents[2] / ".github/workflows/koronos-userspace-acceptance.yml"


def run(target, trace):
    with tempfile.TemporaryDirectory() as td:
        log = Path(td) / "trace.log"
        log.write_text(trace, encoding="utf-8")
        return subprocess.run([sys.executable, str(SCRIPT), target, str(log)], capture_output=True, text=True)


class UserspaceHandoffVerifierTests(unittest.TestCase):
    def test_ring3_probe_and_workflow_use_same_readiness_abi(self):
        probe = USER_INIT_SMOKE.read_text(encoding="utf-8")
        workflow = ACCEPTANCE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('"USERSPACE READY: target=" CHIMERA_TARGET_NAME " init_pid="', probe)
        self.assertIn('USERSPACE READY: target=${TARGET} init_pid=[1-9][0-9]*', workflow)
        self.assertNotIn('USERSPACE READY: ${TARGET} init pid=', workflow)

    def test_kernel_target_marker_matches_verifier_abi(self):
        source = TARGET_LAUNCH.read_text(encoding="utf-8")
        self.assertIn('parse_target_pid_line(bytes,length,"USERSPACE READY: target="," init_pid=",target,pid)', source)

    def test_native_write_validates_complete_user_range_before_read(self):
        source = SYSCALL_SOURCE.read_text(encoding="utf-8")
        start = source.index("case CHM_SYS_WRITE:")
        end = source.index("case CHM_SYS_OPEN:", start)
        write_case = source[start:end]
        validate = "koronos_target_validate_user_range(address, length, 0u)"
        read_user = "koronos_console_write_user(address, length)"
        self.assertIn(validate, write_case)
        self.assertLess(write_case.index(validate), write_case.index(read_user))
        self.assertIn("static_cast<uint64_t>(-14ll)", write_case)

    def test_process_runtime_is_bound_before_running_and_unbound_before_reclaim(self):
        header = PROCESS_HEADER.read_text(encoding="utf-8")
        process = PROCESS_SOURCE.read_text(encoding="utf-8")
        launch = TARGET_LAUNCH.read_text(encoding="utf-8")
        self.assertIn("chimera_process_bind_runtime", header)
        self.assertIn("chimera_process_get_runtime", header)
        self.assertIn("state==CHIMERA_PROCESS_RUNNING&&!slots[i].runtime.bound", process)
        self.assertLess(launch.index("chimera_process_bind_runtime"), launch.index("CHIMERA_PROCESS_RUNNING"))
        exit_start = launch.index("const int exit_code=")
        self.assertLess(launch.index("chimera_process_unbind_runtime(active_pid)", exit_start), launch.index("ops->destroy_address_space(nullptr,loaded.address_space)", exit_start))

    def test_elf_admission_checks_program_header_bounds_and_executable_entry(self):
        process = PROCESS_SOURCE.read_text(encoding="utf-8")
        self.assertIn("h->e_phoff>size", process)
        self.assertIn("h->e_phnum>4096u", process)
        self.assertIn("!entry_executable", process)
        self.assertIn("static bool pid_in_use", process)
        self.assertIn("p.pid=allocate_pid()", process)
    def test_kernel_ready_alone_is_not_userspace_ready(self):
        result = run("live", KERNEL)
        self.assertEqual(result.returncode, 1)
        self.assertIn("user-originated init syscall acknowledgement", result.stdout)

    def test_readiness_marker_without_user_entry_ack_is_rejected(self):
        result = run("live", KERNEL + READY.format(target="live", pid=1))
        self.assertEqual(result.returncode, 1)
        self.assertIn("user-originated init syscall acknowledgement", result.stdout)

    def test_explicit_native_init_blocked_is_reported_as_service_readiness_failure(self):
        trace = KERNEL + ENTRY.format(target="installer", pid=1) + "NATIVE INIT BLOCKED: filesystem service unavailable\n"
        result = run("installer", trace)
        self.assertEqual(result.returncode, 1)
        self.assertIn("production service readiness", result.stdout)
        self.assertIn("NATIVE INIT BLOCKED", result.stdout)
        self.assertNotIn("actual init PID readiness marker", result.stdout)

    def test_requires_matching_target(self):
        trace = KERNEL + ENTRY.format(target="live", pid=1) + READY.format(target="live", pid=1)
        result = run("installer", trace)
        self.assertEqual(result.returncode, 1)
        self.assertIn("ordered kernel-ready -> user-originated init syscall", result.stdout)

    def test_requires_same_pid_for_entry_and_ready(self):
        trace = KERNEL + ENTRY.format(target="live", pid=1) + READY.format(target="live", pid=2)
        self.assertEqual(run("live", trace).returncode, 1)

    def test_requires_ordered_markers(self):
        trace = READY.format(target="live", pid=1) + ENTRY.format(target="live", pid=1) + KERNEL
        self.assertEqual(run("live", trace).returncode, 1)

    def test_accepts_live_with_user_originated_syscall_and_matching_pid(self):
        trace = KERNEL + ENTRY.format(target="live", pid=1) + READY.format(target="live", pid=1)
        self.assertEqual(run("live", trace).returncode, 0)

    def test_rejects_zero_or_mismatched_pid(self):
        self.assertEqual(run("recovery", KERNEL + ENTRY.format(target="live", pid=1) + READY.format(target="live", pid=1)).returncode, 1)
        self.assertEqual(run("recovery", KERNEL + ENTRY.format(target="recovery", pid=0) + READY.format(target="recovery", pid=0)).returncode, 1)

    def test_accepts_recovery_with_nonzero_pid(self):
        trace = KERNEL + ENTRY.format(target="recovery", pid=2) + READY.format(target="recovery", pid=2)
        self.assertEqual(run("recovery", trace).returncode, 0)


if __name__ == "__main__":
    unittest.main()
