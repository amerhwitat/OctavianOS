import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class SharedDesktopIconTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sprite = (ROOT / "desktop/shared-icons/catalog.svg").read_text(encoding="utf-8")
        cls.manifest = json.loads((ROOT / "desktop/shared-icons/manifest.json").read_text(encoding="utf-8"))
        cls.theme = json.loads((ROOT / "desktop/shared-icons/icon-theme.json").read_text(encoding="utf-8"))

    def test_manifest_and_sprite_are_consistent(self):
        self.assertEqual(self.manifest["schema"], "chimera-octavian-app-icons/v1")
        ids = {item["id"] for item in self.manifest["apps"]}
        required = {
            "aurora-files", "chromium", "terminal", "settings", "network",
            "voiceconnect", "system-monitor", "aurora-media-player",
            "store", "about", "docs", "chimera-boot-manager", "archive-manager"
        }
        self.assertTrue(required <= ids)
        for icon_id in required:
            self.assertIn(f'id="app-{icon_id}"', self.sprite)

    def test_theme_maps_both_desktops_to_registered_icons(self):
        self.assertEqual(self.theme["schema"], "CHM-OCTAVIAN-SHARED-ICON-THEME-1")
        ids = {item["id"] for item in self.manifest["apps"]}
        for desktop in ("aurora", "marine"):
            self.assertTrue(self.theme["desktops"][desktop])
            self.assertTrue(set(self.theme["desktops"][desktop].values()) <= ids)

    def test_aurora_shell_uses_semantic_icons_for_desktop_and_launcher(self):
        js = (ROOT / "desktop/aurora-shell/assets/shell.js").read_text(encoding="utf-8")
        css = (ROOT / "desktop/aurora-shell/assets/shell.css").read_text(encoding="utf-8")
        self.assertIn("ICON_SYMBOLS", js)
        self.assertIn("appGlyphNode(icon.glyph, ICON_SYMBOLS[icon.id])", js)
        self.assertIn("../shared-icons/catalog.svg#app-", js)
        self.assertIn("launcherButton(icon.glyph", js)
        self.assertIn(".app-symbol", css)

    def test_xorg_provider_is_declared_and_guarded(self):
        provider = json.loads(
            (ROOT / "vendor/chimera-ii-os/source/desktop/x11/xorg-provider.json").read_text(encoding="utf-8")
        )
        launcher = (ROOT / "vendor/chimera-ii-os/source/desktop/x11/start-session.sh").read_text(encoding="utf-8")
        packages = (ROOT / "vendor/chimera-ii-os/source/tools/commands/install-command-providers.sh").read_text(encoding="utf-8")
        self.assertIn("xserver-xorg", provider["packages"])
        self.assertIn("xwayland", provider["packages"])
        self.assertIn("CHIMERA_X11_RUNTIME_VERIFIED", launcher)
        self.assertIn("CHIMERA_X11_FORCE_UNVERIFIED", launcher)
        self.assertIn("xserver-xorg", packages)

    def test_marine_shortcuts_and_taskbar_use_semantic_icons(self):
        page = (ROOT / "desktop/marine/index.html").read_text(encoding="utf-8")
        self.assertIn("../shared-icons/catalog.svg#app-aurora-files", page)
        self.assertIn("../shared-icons/catalog.svg#app-chromium", page)
        self.assertIn("../shared-icons/catalog.svg#app-terminal", page)
        self.assertIn("../shared-icons/catalog.svg#app-settings", page)
        self.assertIn("class=\"app-icon\"", page)
        self.assertIn(".app-icon{", page)


if __name__ == "__main__":
    unittest.main()
