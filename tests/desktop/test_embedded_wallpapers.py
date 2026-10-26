#!/usr/bin/env python3
"""OctavianOS contract tests for offline embedded wallpaper generation."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/wallpapers"))
from embed_wallpapers import generate, jpeg_dimensions


def fake_jpeg(width: int, height: int) -> bytes:
    sof_payload = bytes([8]) + height.to_bytes(2, "big") + width.to_bytes(2, "big") + bytes([3, 1, 0x11, 0, 2, 0x11, 0, 3, 0x11, 0])
    segment = bytes([0xFF, 0xC0]) + (len(sof_payload) + 2).to_bytes(2, "big") + sof_payload
    return b"\xff\xd8" + segment + b"\xff\xd9"


class EmbeddedWallpaperTests(unittest.TestCase):
    def test_jpeg_dimensions(self):
        self.assertEqual(jpeg_dimensions(fake_jpeg(2048, 1152)), (2048, 1152))

    def test_css_uses_original_jpeg_data_uris_and_dark_fallbacks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "wallpapers"
            source.mkdir()
            (source / "aurora-and-mountain.jpg").write_bytes(fake_jpeg(2048, 1152))
            (source / "octavian-marine-dual-brand.jpg").write_bytes(fake_jpeg(1672, 941))
            result = generate(source, root / "embedded.css", root / "manifest.json")
            css = (root / "embedded.css").read_text()
            self.assertIn("data:image/jpeg;base64,", css)
            self.assertIn("background-size: cover", css)
            self.assertIn("#07121c", css)
            self.assertIn("#070914", css)
            self.assertEqual(len(result["wallpapers"]), 2)

    def test_missing_or_wrong_wallpaper_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "aurora-and-mountain.jpg").write_bytes(fake_jpeg(2048, 1152))
            with self.assertRaises(FileNotFoundError):
                generate(root, root / "embedded.css", root / "manifest.json")
            (root / "octavian-marine-dual-brand.jpg").write_bytes(fake_jpeg(800, 450))
            with self.assertRaisesRegex(ValueError, "expected 1672x941"):
                generate(root, root / "embedded.css", root / "manifest.json")


if __name__ == "__main__":
    unittest.main(verbosity=2)
