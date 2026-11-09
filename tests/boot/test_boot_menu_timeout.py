import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class BootMenuTimeoutTests(unittest.TestCase):
    def assert_menu(self, relative, seconds):
        lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
        self.assertIn(f"set timeout={seconds}", lines, relative)
        self.assertIn("set timeout_style=menu", lines, relative)
        self.assertIn("set default=0", lines, relative)

    def test_octavian_primary_menus_wait_five_minutes(self):
        for path in ("boot/iso/grub.cfg", "boot/jasper/jasper.cfg"):
            with self.subTest(path=path):
                self.assert_menu(path, 300)

    def test_octavian_submenus_wait_two_minutes(self):
        for path in (
            "boot/jasper/live.cfg", "boot/jasper/install.cfg",
            "boot/jasper/recovery.cfg", "boot/jasper/diagnostics.cfg",
            "boot/jasper/safe.cfg", "boot/jasper/retro.cfg",
            "boot/spitfire/spitfire-menu.cfg", "boot/installation/menu.cfg",
        ):
            with self.subTest(path=path):
                self.assert_menu(path, 120)

    def test_vendored_primary_and_submenu_policies(self):
        base = "vendor/chimera-ii-os/source/"
        for path in ("boot/iso/grub.cfg", "boot/loader-menu.cfg", "boot/jasper/jasper.cfg"):
            with self.subTest(path=path):
                self.assert_menu(base + path, 300)
        for path in (
            "boot/spitfire/spitfire-menu.cfg", "boot/installation/menu.cfg",
            "boot/jasper/live.cfg", "boot/jasper/install.cfg",
            "boot/jasper/recovery.cfg", "boot/jasper/diagnostics.cfg",
            "boot/jasper/retro.cfg", "boot/jasper/safe-mode.cfg",
            "boot/jasper/last-known-good.cfg",
        ):
            with self.subTest(path=path):
                self.assert_menu(base + path, 120)

    def test_generated_recovery_menu_uses_two_minute_timeout(self):
        script = (ROOT / "vendor/chimera-ii-os/source/boot/iso/prepare-layout.sh").read_text()
        marker = 'cat > "$DIST/boot/jasper/recovery.cfg" <<\'EOF\''
        self.assertIn(marker, script)
        generated = script.split(marker, 1)[1].split("\nEOF", 1)[0]
        self.assertIn("set timeout=120", generated)
        self.assertIn("set timeout_style=menu", generated)
        self.assertIn("set default=0", generated)

    def test_gates_and_boot_contract_are_in_sync(self):
        base = ROOT / "vendor/chimera-ii-os/source"
        boot = json.loads((base / "boot/boot-menu-contract.json").read_text())
        gates = json.loads((base / "desktop/aurora/gates_menu.json").read_text())
        expected = {
            "timeout_seconds": 300,
            "submenu_timeout_seconds": 120,
            "timeout_style": "menu",
            "default_entry": "live",
            "on_timeout": "boot_default",
        }
        self.assertEqual(boot["menu_policy"], expected)
        self.assertEqual(gates["boot_contract"]["menu_policy"], expected)


if __name__ == "__main__":
    unittest.main()
