#!/usr/bin/env python3
"""Validate cross-OS app/settings/driver/CPU compatibility contracts."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPAT = ROOT / "config/platform/os-compatibility.json"
DRIVER = ROOT / "config/hardware/driver-assistant-policy.json"
SETTINGS = ROOT / "config/settings/control-panel-registry.json"
CATALOG = ROOT / "docs/OPEN_SOURCE_USERSPACE_CATALOG.json"

def load(path):
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise SystemExit(f"invalid schema envelope: {path.relative_to(ROOT)}")
    return value

compat = load(COMPAT)
driver = load(DRIVER)
settings = load(SETTINGS)
catalog = load(CATALOG)

allowed = set(compat["rules"]["status_values"])
assert compat["rules"]["default_status"] in allowed
os_entries = compat["operating_system_families"]
os_ids = [entry["id"] for entry in os_entries]
assert len(os_ids) == len(set(os_ids)), "duplicate OS family IDs"
for entry in os_entries:
    status = entry.get("status", entry.get("support_mode", "not_tested"))
    assert status in allowed, f"invalid compatibility status for {entry['id']}: {status}"
for required in ("chimera", "octavian", "linux", "windows", "macos"):
    assert required in os_ids, f"missing OS family: {required}"
for entry in compat["cpu_profiles"]:
    assert entry["status"] in allowed, f"invalid CPU status for {entry['id']}"

sections = settings["sections"]
section_ids = [section["id"] for section in sections]
assert len(section_ids) == len(set(section_ids)), "duplicate settings section IDs"
setting_ids = [setting for section in sections for setting in section["settings"]]
assert len(setting_ids) == len(set(setting_ids)), "duplicate setting IDs"
for required in ("devices", "compatibility", "applications", "security", "platform_specific"):
    assert required in section_ids, f"missing control-panel section: {required}"
assert settings["apply_contract"]["no_silent_fallback"] is True

for required in ("inventory", "catalog_match", "policy_check", "sandbox_probe", "acceptance", "audit"):
    assert any(step["name"] == required for step in driver["pipeline"]), f"missing driver pipeline step: {required}"
for forbidden in ("load_or_execute_model_generated_kernel_code", "bypass_signature_or_trust_policy"):
    assert forbidden in driver["model_role"]["forbidden"], f"missing safety guard: {forbidden}"
assert driver["learning_policy"]["offline_first"] is True
assert driver["implementation_status"] == "policy_only_no_RNN_or_LLM_inference_backend_linked"
assert "bound_verified" in driver["driver_states"]

families = catalog["application_families"]
family_ids = [family["id"] for family in families]
assert len(family_ids) == len(set(family_ids)), "duplicate application family IDs"
target_matrix = catalog["target_os_matrix"]
target_ids = [target["id"] for target in target_matrix]
assert len(target_ids) == len(set(target_ids)), "duplicate app target IDs"
for required in ("chimera", "octavian", "linux", "windows", "macos"):
    assert required in target_ids, f"missing app target: {required}"
for target in target_matrix:
    assert target["status"] == "candidate_only" and target["provider_required"] is True, (
        f"target {target['id']} must remain gated on provider and evidence"
    )
for family in families:
    assert family.get("status") == "candidate_only", (
        f"application family {family['id']} must remain candidate-only until target validation"
    )
    for app in family.get("examples", []):
        assert app.get("name") and app.get("source"), (
            f"application example in {family['id']} needs a name and upstream source"
        )

# Keep the scheduler's SMP claim honest: serial stepping is not parallel execution.
SCHEDULER = ROOT / "vendor/chimera-ii-os/source/kernel/core/scheduler.cpp"
scheduler_source = SCHEDULER.read_text(encoding="utf-8")
parallel_signature = 'extern "C" uint32_t chimera_sched_run_parallel('
assert parallel_signature in scheduler_source, f"missing parallel scheduler entry: {SCHEDULER}"
parallel_body = scheduler_source.split(parallel_signature, 1)[1].split("\n}", 1)[0]
assert "chimera_sched_run_once(" not in parallel_body, (
    "run_parallel must not disguise serial callback stepping as SMP"
)
assert "chimera_sched_run_serial_range(" not in parallel_body, (
    "run_parallel must not delegate to the serial stepping helper"
)
assert "return 0;" in parallel_body, (
    "parallel dispatch must fail closed until independent AP workers are implemented"
)

# Parallel-for must not disguise serial chunk iteration as concurrent execution.
PARALLEL_SOURCE = ROOT / "vendor/chimera-ii-os/source/kernel/core/parallel.cpp"
parallel_source = PARALLEL_SOURCE.read_text(encoding="utf-8")
assert "if (workers > 1) return 0;" in parallel_source, (
    "multi-worker parallel_for requests must fail closed until AP-backed dispatch exists"
)
assert "for (uint32_t i = begin; i < end; ++i)" in parallel_source, (
    "single-worker fallback must be explicit and reviewable"
)

# Production payload data is not an executable native init. Require the
# launcher to fail closed and name the missing USER_INIT_ELF integration.
TARGET_LAUNCH = ROOT / "vendor/chimera-ii-os/source/kernel/core/target_launch.cpp"
target_launch_source = TARGET_LAUNCH.read_text(encoding="utf-8")
assert "no native USER_INIT_ELF module was staged" in target_launch_source, (
    "production payload without a native init ELF must report the concrete handoff failure"
)
assert "CHIMERA_MODULE_RECOVERY_INITRAMFS" in target_launch_source and "CHIMERA_MODULE_INSTALL_IMAGE" in target_launch_source, (
    "missing native init detection must cover Live, Recovery, and Installer payloads"
)

# Production native init is a separate freestanding artifact, not the candidate probe.
NATIVE_INIT = ROOT / "vendor/chimera-ii-os/source/kernel/userspace/native_init.c"
NATIVE_LINKER = ROOT / "vendor/chimera-ii-os/source/kernel/userspace/native_init_linker.ld"
NATIVE_BUILD = ROOT / "vendor/chimera-ii-os/source/kernel/build-koronos.sh"
PRODUCTION_GRUB = ROOT / "vendor/chimera-ii-os/source/boot/iso/grub.cfg"
assert NATIVE_INIT.is_file() and NATIVE_LINKER.is_file(), "production native init source/linker layout missing"
native_init_source = NATIVE_INIT.read_text(encoding="utf-8")
assert 'int $0x80' in native_init_source and "CHM_SYS_GETPID" in native_init_source and "CHM_SYS_WRITE" in native_init_source, (
    "native init must execute the CPL3 gate and use the actual Koronos native syscall ABI"
)
assert "CHM_SYS_VALIDATE_BOOT_PAYLOAD" in native_init_source and "CHM_SYS_VALIDATE_BOOT_PAYLOAD" in target_launch_source or "koronos_target_validate_boot_payload" in target_launch_source, (
    "native init must validate the selected production payload before readiness"
)
assert "VFS mounting, storage" in native_init_source and "service supervision and desktop readiness" in native_init_source, (
    "native init must not overclaim VFS/storage/desktop readiness that is not implemented"
)
native_build_source = NATIVE_BUILD.read_text(encoding="utf-8")
assert "kernel/userspace/native_init.c" in native_build_source and "native-init-$target.elf" in native_build_source, (
    "build must compile dedicated production init ELFs, not copy acceptance probes"
)
production_grub_source = PRODUCTION_GRUB.read_text(encoding="utf-8")
for target in ("live", "installer", "recovery"):
    assert f"native-init-{target}.elf" in production_grub_source, (
        f"production GRUB must stage native init for {target}"
    )

NATIVE_ACCEPTANCE_WORKFLOW = ROOT / ".github/workflows/koronos-userspace-acceptance.yml"
acceptance_workflow_source = NATIVE_ACCEPTANCE_WORKFLOW.read_text(encoding="utf-8")
assert 'module2 /boot/native-init-$TARGET.elf chimera-user-init-elf target=$TARGET' in acceptance_workflow_source, (
    "six-case acceptance must boot the production native init, not the candidate probe"
)
assert 'cp "$NATIVE_INIT" "$ISO_ROOT/boot/native-init-$TARGET.elf"' in acceptance_workflow_source, (
    "six-case acceptance ISO must stage the target-specific native init artifact"
)

app_count = sum(len(family.get("examples", [])) for family in families)
print(f"cross-OS contracts PASS: {len(os_entries)} OS families, "
      f"{len(compat['cpu_profiles'])} CPU profiles, {len(setting_ids)} settings, "
      f"{len(families)} app families/{app_count} candidate apps, "
      f"{len(driver['pipeline'])} driver-assistant stages (policy only)")
