#!/usr/bin/env python3
"""Source contract for target-matched native init + production payload routing.

This is a structural regression test, not production boot acceptance. Runtime
acceptance still requires the unchanged six-case ISO verifier.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "kernel/core/target_launch.cpp"
text = SOURCE.read_text(encoding="utf-8")

required = [
    "uint32_t payload_count=0;",
    "Target payload_target=TARGET_NONE;",
    "case CHIMERA_MODULE_LIVE_INITRAMFS:",
    "case CHIMERA_MODULE_INSTALL_IMAGE:",
    "case CHIMERA_MODULE_RECOVERY_INITRAMFS:",
    "if (payload_count>1u)",
    "if (payload_count==1u && payload_target!=target)",
    "native init target does not match the selected production payload",
    "stage_rootfs(archive_bytes, archive->size)",
    'chimera_vfs_mount("/", &ramfs_vfs_ops, staged_rootfs, CHIMERA_VFS_MOUNT_RDONLY)',
    'chimera_vfs_mount("/tmp", chimera_tmpfs_vfs_ops(), tmpfs_candidate, 0u)',
    "transactional RAMFS staging failed; no rootfs was published",
    "VFS root mount failed; refusing userspace launch",
]
missing = [item for item in required if item not in text]
if missing:
    raise SystemExit("target-launch native-init contract missing: " + "; ".join(missing))

# The target-specific ELF is explicit and independently bound to one payload.
if "if (count!=1" not in text or "USER_INIT_ELF module was supplied" not in text:
    raise SystemExit("target/payload dispatch must reject missing or ambiguous native init ELF")
if "chimera_initramfs_find_elf" in text:
    raise SystemExit("embedded CPIO ELF fallback must remain disabled")
print("target-launch native-init contract: PASS (source-level only; not boot acceptance)")
