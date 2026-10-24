#!/usr/bin/env python3
"""Static regression guard for production target payload/init binding (not runtime proof)."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    launch_path = ROOT / "kernel/core/target_launch.cpp"
    if not launch_path.is_file():
        print("TARGET INIT PAYLOAD BINDING FAIL: target launcher missing", file=sys.stderr)
        return 1
    launch = launch_path.read_text(encoding="utf-8")
    required = (
        'chimera_cpio_lookup_executable_newc(archive, archive_size, "/init", &entry)',
        "archive /init is a script",
        "refusing to substitute a separate init ELF",
        "CHIMERA_MODULE_USER_INIT_ELF",
        "CHIMERA_MODULE_LIVE_INITRAMFS",
        "CHIMERA_MODULE_RECOVERY_INITRAMFS",
        "stage_archive_init_elf",
        "stage_rootfs(",
        "chimera_vfs_mount(\"/\", &ramfs_vfs_ops, staged_rootfs, CHIMERA_VFS_MOUNT_RDONLY)",
        'chimera_vfs_mount("/tmp", chimera_tmpfs_vfs_ops(), tmpfs_candidate, 0u)',
        "__atomic_store_n(&published_rootfs, staged_rootfs, __ATOMIC_RELEASE)",
        "production rootfs staging is absent; refusing userspace launch",
        "remain fail-closed",
    )
    for token in required:
        if token not in launch:
            print(f"TARGET INIT PAYLOAD BINDING FAIL: missing contract: {token}", file=sys.stderr)
            return 1
    print("TARGET INIT PAYLOAD BINDING PASS: archive /init, root mount, and writable /tmp are source-wired; runtime proof remains separate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
