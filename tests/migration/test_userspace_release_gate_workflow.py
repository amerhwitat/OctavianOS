"""Regression tests for fail-closed userspace and production DAPS release gates."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/native-koronos-build.yml"
PROCESS_SOURCE = ROOT / "vendor/chimera-ii-os/source/kernel/core/process.cpp"
ELF_SOURCE = ROOT / "vendor/chimera-ii-os/source/kernel/core/elf64.cpp"
LOADER_SOURCE = ROOT / "vendor/chimera-ii-os/source/kernel/core/process_loader.cpp"
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
        elf = ELF_SOURCE.read_text(encoding="utf-8")
        loader = LOADER_SOURCE.read_text(encoding="utf-8")
        self.assertIn("h.e_phentsize != sizeof(koronos_elf64_phdr)", elf)
        self.assertIn("h.e_phnum > (size - h.e_phoff) / sizeof(koronos_elf64_phdr)", elf)
        self.assertIn("const uint64_t phbytes=(uint64_t)h.e_phnum*h.e_phentsize", loader)
        self.assertIn("inside(h.e_phoff,phbytes,image_size)", loader)
        self.assertIn("__builtin_memcpy(&ph,bytes+h.e_phoff+(uint64_t)i*h.e_phentsize,sizeof(ph))", loader)

    def test_elf_entry_must_be_executable_and_load_ranges_must_not_overlap(self):
        process = PROCESS_SOURCE.read_text(encoding="utf-8")
        loader = LOADER_SOURCE.read_text(encoding="utf-8")
        self.assertIn("bool entry_executable = false", process)
        self.assertIn("!entry_executable", process)
        self.assertIn("Refuse page-rounded overlap: permission merging must be an explicit mapper policy.", loader)
        self.assertIn("!user_addr(ph.p_vaddr)", loader)
        self.assertIn("!user_addr(end-1u)", loader)
        self.assertIn("high>stack_base&&low<stack_top", loader)

    def test_parallel_scheduler_does_not_claim_serial_steps_as_smp(self):
        source = SCHEDULER_SOURCE.read_text(encoding="utf-8")
        body = source.split("extern \"C\" uint32_t chimera_sched_run_parallel", 1)[1]
        body = body.split("extern \"C\"", 1)[0]
        self.assertIn("Never report serial callback invocations as parallel execution.", body)
        self.assertIn("return 0;", body)
        self.assertNotIn("chimera_sched_run_once(cpu)", body)

    def test_pid_exhaustion_fails_closed_without_reuse(self):
        source = PROCESS_SOURCE.read_text(encoding="utf-8")
        self.assertIn("if (next_pid == 0 || next_pid > 0x7FFFFFFFu) return -11;", source)
        self.assertIn("Never wrap into an identity that may still be live", source)
        self.assertIn("slots[i].used", source)
        self.assertNotIn("static bool pid_in_use(uint32_t pid)", source)


if __name__ == "__main__":
    unittest.main()
