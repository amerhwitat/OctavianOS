#!/usr/bin/env python3
"""Static regression test for OctavianOS installer menu payload routing.

This checks source contracts only; it does not replace GRUB parsing or QEMU boot.
"""
from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[2]

def require(ok, message):
    if not ok:
        raise SystemExit("installer routing regression: " + message)

def menu_block(text, menu_id):
    match = re.search(
        r'menuentry\s+"[^"]*"\s+--id\s+' + re.escape(menu_id) +
        r'\s*\{(.*?)\n\}', text, re.S
    )
    require(match is not None, f"menu entry --id {menu_id} is missing")
    return match.group(1)

def main():
    grub = (ROOT / "boot/iso/grub.cfg").read_text()
    jasper = (ROOT / "boot/jasper/jasper.cfg").read_text()
    installer = (ROOT / "boot/jasper/install.cfg").read_text()

    top_install = menu_block(grub, "install")
    require("configfile /boot/jasper/install.cfg" in top_install,
            "top-level Install entry must hand off to Jasper's installer menu")
    require("chimera-live-initramfs.img" not in top_install,
            "top-level Install entry must never pass the live initramfs")
    require("chimera-live-manifest.json" not in top_install,
            "top-level Install entry must never pass the live manifest")
    require("refusing to boot the Live image as an installer" in top_install,
            "missing installer media must fail closed with a useful message")

    jasper_install = menu_block(jasper, "chimera-install")
    require("configfile /boot/jasper/install.cfg" in jasper_install,
            "Jasper installer menu target must load install.cfg")

    native_installer = menu_block(installer, "installer")
    require("/install/installer/installation.img" in native_installer,
            "native installer payload check is missing")
    require("module2 /install/installer/installation.img chimera-installation-image" in native_installer,
            "native installation image is not passed to Koronos")
    require("module2 /install/installer/installation-manifest.json chimera-installation-manifest" in native_installer,
            "installer manifest is not passed to Koronos")
    require("module2 /install/installer/installer-contract.json chimera-installer-contract" in native_installer,
            "installer contract is not passed to Koronos")
    require("chimera-live-initramfs.img" not in native_installer,
            "native installer path must not substitute live initramfs")

    # Keep current kernel ABI module names until the kernel classifier is migrated.
    require("chimera-installation-image" in native_installer,
            "kernel module ABI name unexpectedly changed")
    print("installer routing static contract: PASS (not a QEMU/runtime claim)")

if __name__ == "__main__":
    main()
