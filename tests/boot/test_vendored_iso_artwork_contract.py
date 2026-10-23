#!/usr/bin/env python3
"""Regression guard for Octavian artwork and native-init ISO build contracts."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
ISO_BUILDER = ROOT / "vendor/chimera-ii-os/source/boot/iso/build-iso.sh"
KERNEL_BUILDER = ROOT / "vendor/chimera-ii-os/source/kernel/build-koronos.sh"
NATIVE_WORKFLOW = ROOT / ".github/workflows/octavian-chimera-integration.yml"


class VendoredIsoArtworkContractTests(unittest.TestCase):
    def test_octavian_artwork_uses_checkout_root_and_is_staged_before_mastering(self):
        source = ISO_BUILDER.read_text(encoding="utf-8")
        required = (
            'git -C "$ROOT" rev-parse --show-toplevel',
            'desktop/aurora/assets/octavian-octopus-aurora.svg',
            'tools/boot/render_boot_artwork.py',
            'octavian-octopus-aurora.png',
            'octavian-artwork-manifest.json',
            'Octavian artwork PNG was not staged before ISO mastering.',
            'grub-mkrescue -o "$DIST/output.iso" "$DIST/iso"',
        )
        for item in required:
            with self.subTest(contract=item):
                self.assertIn(item, source)
        self.assertLess(source.index('Octavian artwork PNG was not staged before ISO mastering.'),
                        source.index('grub-mkrescue -o "$DIST/output.iso" "$DIST/iso"') + 600)

    def test_native_build_requires_target_specific_probe_outputs(self):
        source = KERNEL_BUILDER.read_text(encoding="utf-8")
        for target in ("live", "installer", "recovery"):
            with self.subTest(target=target):
                self.assertIn(f'user-init-${{target}}.elf', source)
        workflow = NATIVE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('artifact="build/koronos/x86_64/user-init-$target.elf"', workflow)
        self.assertIn("Canonical Koronos build omitted candidate artifact", workflow)


if __name__ == "__main__":
    unittest.main()
