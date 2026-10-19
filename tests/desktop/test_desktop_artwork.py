import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class DesktopArtworkTests(unittest.TestCase):
    def test_wallpaper_catalog_has_sources_and_license(self):
        catalog = json.loads((ROOT / "desktop/artwork/wallpapers.json").read_text())
        self.assertEqual(catalog["delivery"], "remote-prototype")
        self.assertGreaterEqual(len(catalog["wallpapers"]), 2)
        ids = {item["id"] for item in catalog["wallpapers"]}
        self.assertIn("aurora-ocean-night", ids)
        self.assertIn("marine-turtle-reef", ids)
        for item in catalog["wallpapers"]:
            self.assertTrue(item["image_url"].startswith("https://images.unsplash.com/"))
            self.assertTrue(item["source_page"].startswith("https://unsplash.com/"))
            self.assertEqual(item["license"], "Unsplash License")
            self.assertTrue(item["fallback"])

    def test_aurora_name_and_macos_layout_contract(self):
        page = (ROOT / "desktop/aurora-wayland-glass/index.html").read_text()
        self.assertIn("Aurora Wayland Glass Desktop", page)
        self.assertIn("dockwrap", page)
        self.assertIn("global menu bar", page)
        # The desktop now prefers the 4K scalable artwork; retain the original
        # source asset in the repo for existing consumers and backward compatibility.
        self.assertIn("../aurora/assets/octavian-celestial-octopus-3840x2160.svg", page)
        self.assertTrue((ROOT / "desktop/aurora/assets/octavian-celestial-octopus-3840x2160.svg").is_file())
        self.assertTrue((ROOT / "desktop/aurora/assets/octavian-octopus-aurora.svg").is_file())
        manifest = json.loads((ROOT / "desktop/aurora/assets/octavian-artwork-manifest.json").read_text())
        self.assertTrue(any(item["path"] == "desktop/aurora/assets/octavian-celestial-octopus-3840x2160.svg" for item in manifest["artworks"]))

    def test_marine_windows_style_layout_contract(self):
        page = (ROOT / "desktop/marine/index.html").read_text()
        self.assertIn("Marine Desktop", page)
        self.assertIn("startmenu", page)
        self.assertIn("taskbar", page)
        self.assertIn("images.unsplash.com/photo-1717293520171-b1d8b5d5e3f2", page)
        self.assertIn("no session launched", page)

    def test_no_obsolete_aurora_background_scheme(self):
        docs = (ROOT / "desktop/artwork/README.md").read_text()
        self.assertIn("Do not reintroduce the obsolete aurora-background.jpg", docs)


if __name__ == "__main__":
    unittest.main()
