#!/usr/bin/env python3
"""Prevent production GRUB entries from omitting their target-matched native init ELF."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
CONFIGS = (
    ROOT / "boot/iso/grub.cfg",
    ROOT / "boot/jasper/live.cfg",
    ROOT / "boot/jasper/safe.cfg",
    ROOT / "boot/jasper/recovery.cfg",
    ROOT / "boot/jasper/diagnostics.cfg",
    ROOT / "boot/jasper/install.cfg",
    ROOT / "vendor/chimera-ii-os/source/boot/jasper/live.cfg",
    ROOT / "vendor/chimera-ii-os/source/boot/jasper/recovery.cfg",
    ROOT / "vendor/chimera-ii-os/source/boot/jasper/install.cfg",
    ROOT / "vendor/chimera-ii-os/source/boot/iso/grub.cfg",
)


def entries(text):
    chunks = []
    current = []
    for line in text.splitlines():
        if line.lstrip().startswith("menuentry ") and current:
            chunks.append("\n".join(current))
            current = []
        current.append(line)
    if current:
        chunks.append("\n".join(current))
    return chunks


class NativeInitModuleRoutingTests(unittest.TestCase):
    def test_every_live_archive_module_has_live_native_init(self):
        for path in CONFIGS:
            lines = path.read_text(encoding="utf-8").splitlines()
            for i, line in enumerate(lines):
                if "module2 /boot/live/chimera-live-initramfs.img" in line:
                    following = "\n".join(lines[i + 1:i + 3])
                    self.assertIn(
                        "module2 /boot/live/user-init-live.elf chimera-user-init-elf target=live",
                        following,
                        f"{path.relative_to(ROOT)}:{i + 1} omits target-matched Live init ELF",
                    )

    def test_every_recovery_archive_module_has_recovery_native_init(self):
        for path in CONFIGS:
            lines = path.read_text(encoding="utf-8").splitlines()
            for i, line in enumerate(lines):
                if "module2 /boot/recovery/chimera-recovery-initramfs.img" in line:
                    following = "\n".join(lines[i + 1:i + 3])
                    self.assertIn(
                        "module2 /boot/recovery/user-init-recovery.elf chimera-user-init-elf target=recovery",
                        following,
                        f"{path.relative_to(ROOT)}:{i + 1} omits target-matched Recovery init ELF",
                    )

    def test_installation_image_entry_requires_and_passes_installer_init(self):
        for path in CONFIGS:
            for entry in entries(path.read_text(encoding="utf-8")):
                if "module2 /install/installer/installation.img chimera-installation-image" not in entry:
                    continue
                self.assertIn("/boot/installer/user-init-installer.elf", entry,
                              f"{path.relative_to(ROOT)} installer entry omits native init ELF")
                self.assertIn("chimera-user-init-elf target=installer", entry,
                              f"{path.relative_to(ROOT)} installer entry has no target binding")
                self.assertIn("/boot/installer/user-init-installer.elf", entry.split("then", 1)[0],
                              f"{path.relative_to(ROOT)} installer entry does not guard the native init file")


if __name__ == "__main__":
    unittest.main()
