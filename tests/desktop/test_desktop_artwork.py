import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class DesktopArtworkTests(unittest.TestCase):
    def test_wallpaper_catalog_has_sources_and_license(self):
        catalog = json.loads((ROOT / "desktop/artwork/wallpapers.json").read_text())
        self.assertEqual(catalog["delivery"], "vendored-source-assets-plus-remote-catalog")
        self.assertGreaterEqual(len(catalog["wallpapers"]), 4)
        ids = {item["id"] for item in catalog["wallpapers"]}
        self.assertIn("octavian-aurora-glass", ids)
        self.assertIn("octavian-marine-productivity", ids)
        self.assertIn("octavian-mobile-edition", ids)
        self.assertIn("aurora-ocean-night", ids)
        self.assertIn("marine-turtle-reef", ids)

        for item in catalog["wallpapers"]:
            if item.get("source") == "repository":
                asset = ROOT / item["path"]
                self.assertTrue(asset.is_file(), item["path"])
                self.assertEqual(item["license"], "CC0-1.0")
                self.assertEqual(item["format"], "svg")
            else:
                self.assertTrue(item["image_url"].startswith("https://images.unsplash.com/"))
                self.assertTrue(item["source_page"].startswith("https://unsplash.com/"))
                self.assertEqual(item["license"], "Unsplash License")
                self.assertTrue(item["fallback"])
                self.assertTrue(item.get("remote_opt_in"))

    def test_aurora_name_and_macos_layout_contract(self):
        page = (ROOT / "desktop/aurora-wayland-glass/index.html").read_text()
        self.assertIn("Aurora Wayland Glass Desktop", page)
        self.assertIn("dockwrap", page)
        self.assertIn("global menu bar", page)
        self.assertIn("../aurora/assets/octavian-octopus-aurora.svg", page)
        self.assertTrue((ROOT / "desktop/aurora/assets/octavian-octopus-aurora.svg").is_file())
        self.assertTrue((ROOT / "desktop/aurora/assets/octavian-artwork-manifest.json").is_file())

    def test_marine_windows_style_layout_contract(self):
        page = (ROOT / "desktop/marine/index.html").read_text()
        self.assertIn("Marine Desktop", page)
        self.assertIn("startmenu", page)
        self.assertIn("taskbar", page)
        self.assertIn('url("assets/octavian-marine-productivity.svg")', page)
        self.assertIn('data-wallpaper="marine"', page)
        self.assertIn('data-wallpaper="aurora"', page)
        self.assertIn("wallpaperPicker", page)
        self.assertNotIn("images.unsplash.com/photo-1717293520171-b1d8b5d5e3f2", page)
        self.assertTrue((ROOT / "desktop/marine/assets/octavian-marine-productivity.svg").is_file())
        self.assertIn("no session launched", page)

    def test_no_obsolete_aurora_background_scheme(self):
        docs = (ROOT / "desktop/artwork/README.md").read_text()
        self.assertIn("Do not reintroduce the obsolete aurora-background.jpg", docs)


if __name__ == "__main__":
    unittest.main()
