#!/usr/bin/env python3
"""Vendored installer menu must route Koronos to the installer target only."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
GRUB = (ROOT / "boot/iso/grub.cfg").read_text()


class InstallerTargetRoutingContract(unittest.TestCase):
    def test_installer_menu_does_not_launch_live_init(self):
        start = GRUB.index('--id install {')
        end = GRUB.index('\n}', start)
        entry = GRUB[start:end]
        self.assertIn("target=installer", entry)
        self.assertNotIn("target=live", entry)
        self.assertIn("module2 /boot/installer/user-init-installer.elf", entry)
        self.assertNotIn("/boot/live/user-init-live.elf", entry)
        self.assertIn("/install/installer/installation.img", entry)


if __name__ == "__main__":
    unittest.main(verbosity=2)
