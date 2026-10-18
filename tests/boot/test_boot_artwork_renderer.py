#!/usr/bin/env python3
from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from tools.boot.render_boot_artwork import DEFAULT_SOURCE, render


class BootArtworkRendererTests(unittest.TestCase):
    def test_source_svg_exists(self):
        self.assertTrue(DEFAULT_SOURCE.is_file(), str(DEFAULT_SOURCE))
        self.assertGreater(DEFAULT_SOURCE.stat().st_size, 100)

    def test_render_produces_firmware_friendly_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "boot" / "octavian-octopus-aurora.png"
            result = render(DEFAULT_SOURCE, output, 1280, 720)
            data = output.read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(struct.unpack(">II", data[16:24]), (1280, 720))
            self.assertEqual(result["width"], 1280)
            self.assertEqual(result["height"], 720)
            self.assertGreater(result["bytes"], 1024)


if __name__ == "__main__":
    unittest.main(verbosity=2)
