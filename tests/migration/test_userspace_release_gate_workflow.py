"""Regression tests for fail-closed userspace and production DAPS release gates."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/native-koronos-build.yml"
PROCESS_SOURCE = ROOT / "vendor/chimera-ii-os/source/kernel/core/process.cpp"
SCHEDULER_SOURCE = ROOT / "vendor/chimera-ii-os/source/kernel/core/scheduler.cpp"


class UserspaceReleaseWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_userspace_gate_is_a_separate_job_after_iso_build(self):
        self.assertIn("  verify-userspace-handoff:", self.text)
        self.assertIn("needs: build-koronos", self.text)
        self.assertIn("python3 tests/migration/verify-userspace-handoff.py live trace/full-iso-debugcon.log", self.text)
        self.assertIn("python3 tests/migration/verify-userspace-handoff.py installer trace/installer-debugcon.log", self.text)
        self.assertIn("python3 tests/migration/verify-userspace-handoff.py recovery trace/recovery-debugcon.log", self.text)

    def test_release_depends_on_userspace_and_production_daps_gates(self):
        section = self.text.split("  publish-native-iso:", 1)[1]
        self.assertIn(
            "needs: [build-koronos, verify-userspace-handoff, verify-production-daps]",
            section,
        )
        self.assertIn("  verify-production-daps:", self.text)
        self.assertIn(
            "python3 tools/release/verify-production-daps.py --evidence production-daps/evidence.json",
            self.text,
        )
        self.assertIn("if: github.event_name == 'push' && github.ref == 'refs/heads/main'", section)
        self.assertIn(
            "Published only after Live/Installer/Recovery userspace handoff and production DAPS evidence gates pass.",
            section,
        )

    def test_build_uploads_each_real_target_trace(self):
        section = self.text.split("      - name: Upload Live, Installer, and Recovery QEMU traces", 1)[1]
        section = section.split("      - name:", 1)[0]
        for trace in ("full-iso-debugcon.log", "installer-debugcon.log", "recovery-debugcon.log"):
            self.assertIn(trace, section)

    def test_process_admission_bounds_program_header_table(self):
        source = PROCESS_SOURCE.read_text(encoding="utf-8")
        self.assertIn("h->e_phentsize != sizeof(koronos_elf64_phdr)", source)
        self.assertIn("in(h->e_phoff, ph_bytes, size)", source)
        self.assertIn("reinterpret_cast<const koronos_elf64_phdr *>(bytes + h->e_phoff)", source)

    def test_elf_entry_must_be_executable_and_load_ranges_must_not_overlap(self):
        source = PROCESS_SOURCE.read_text(encoding="utf-8")
        self.assertIn("bool entry_executable = false", source)
        self.assertIn("!entry_executable", source)
        self.assertIn("Reject page-overlapping PT_LOAD ranges", source)
        self.assertIn("s.p_vaddr < 0x0000000100000000ull", source)
        self.assertIn("end > 0x0000800000000000ull", source)

    def test_parallel_scheduler_does_not_claim_serial_steps_as_smp(self):
        source = SCHEDULER_SOURCE.read_text(encoding="utf-8")
        body = source.split("extern \"C\" uint32_t chimera_sched_run_parallel", 1)[1]
        body = body.split("extern \"C\"", 1)[0]
        self.assertIn("fail-closed until AP startup", body)
        self.assertIn("return 0;", body)
        self.assertNotIn("chimera_sched_run_once(cpu)", body)

    def test_pid_wraparound_does_not_alias_a_live_process(self):
        source = PROCESS_SOURCE.read_text(encoding="utf-8")
        self.assertIn("static bool pid_in_use(uint32_t pid)", source)
        self.assertIn("static uint32_t allocate_pid()", source)
        self.assertIn("!pid_in_use(candidate)", source)


if __name__ == "__main__":
    unittest.main()
