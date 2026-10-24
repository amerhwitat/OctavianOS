#!/usr/bin/env python3
"""Static regression guard for native-init selection and rootfs mounting (not runtime proof)."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> int:
    print(f"TARGET INIT PAYLOAD BINDING FAIL: {message}", file=sys.stderr)
    return 1


def main() -> int:
    launch_path = ROOT / "kernel/core/target_launch.cpp"
    if not launch_path.is_file():
        return fail("target launcher missing")
    launch = launch_path.read_text(encoding="utf-8")
    required = (
        "CHIMERA_MODULE_USER_INIT_ELF",
        "CHIMERA_MODULE_LIVE_INITRAMFS",
        "CHIMERA_MODULE_RECOVERY_INITRAMFS",
        "const void *init_image = reinterpret_cast<const void *>(static_cast<uintptr_t>(selected->base));",
        "const uint64_t init_image_size = selected->size;",
        "stage_rootfs(",
        'chimera_vfs_mount("/", &ramfs_vfs_ops, staged_rootfs, CHIMERA_VFS_MOUNT_RDONLY)',
        'chimera_vfs_mount("/tmp", chimera_tmpfs_vfs_ops(), tmpfs_candidate, 0u)',
        "__atomic_store_n(&published_rootfs, staged_rootfs, __ATOMIC_RELEASE)",
        "production rootfs staging is absent; refusing userspace launch",
        "remain fail-closed",
    )
    for token in required:
        if token not in launch:
            return fail(f"missing contract: {token}")
    forbidden = (
        "stage_archive_init_elf",
        "staged_archive_init",
        'chimera_cpio_lookup_executable_newc(archive, archive_size, "/init", &entry)',
        "refusing to substitute a separate init ELF",
    )
    for token in forbidden:
        if token in launch:
            return fail(f"archive /init must not override the tagged native ELF: {token}")
    print("TARGET INIT PAYLOAD BINDING PASS: tagged native ELF selection and rootfs mount are source-wired; runtime proof remains separate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
