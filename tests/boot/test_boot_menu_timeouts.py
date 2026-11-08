#!/usr/bin/env python3
"""Contract test for long interactive Jasper/Gates/GRUB boot menus."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"vendor/chimera-ii-os/source" if (ROOT/"vendor/chimera-ii-os/source").is_dir() else ROOT
BOOT=SOURCE/"boot"
PRIMARY=("iso/grub.cfg","jasper/jasper.cfg","spitfire/spitfire-menu.cfg","loader-menu.cfg")
SUBMENUS=("installation/menu.cfg","installation/services.cfg","jasper/diagnostics.cfg","jasper/install.cfg",
          "jasper/last-known-good.cfg","jasper/live.cfg","jasper/recovery.cfg","jasper/retro.cfg","jasper/safe-mode.cfg")
def timeout(path):
    text=path.read_text(encoding="utf-8")
    match=re.search(r"^\s*set timeout=(\d+)\s*$",text,re.M)
    assert match, f"{path}: no explicit GRUB timeout"
    assert re.search(r"^\s*set timeout_style=menu\s*$",text,re.M), f"{path}: timeout_style must remain menu"
    return int(match.group(1))
for rel in PRIMARY:
    actual=timeout(BOOT/rel)
    assert actual==300, f"{rel}: expected 300 seconds, got {actual}"
for rel in SUBMENUS:
    actual=timeout(BOOT/rel)
    assert actual==300, f"{rel}: expected 300 seconds, got {actual}"
# The ISO menu must accept both physical keyboard and serial-console input.
# This is required for remote/headless machines and deterministic QEMU menu tests.
grub_menu=(BOOT/"iso/grub.cfg").read_text(encoding="utf-8")
assert re.search(r"^\s*serial --unit=0 --speed=115200\s*$",grub_menu,re.M), "GRUB serial device is not configured"
assert re.search(r"^\s*terminal_input serial console\s*$",grub_menu,re.M), "GRUB menu must accept serial and local keyboard input"
# The OctavianOS repository has its own Jasper/GRUB menus in addition to
# the vendored Chimera boot tree. Validate both; never let SOURCE selection
# silently leave the product's own menus outside the timeout gate.
if SOURCE != ROOT:
    OCTAVIAN_PRIMARY=("iso/grub.cfg","jasper/jasper.cfg","spitfire/spitfire-menu.cfg")
    OCTAVIAN_SUBMENUS=("installation/menu.cfg","jasper/diagnostics.cfg","jasper/install.cfg",
                       "jasper/live.cfg","jasper/recovery.cfg","jasper/retro.cfg")
    for rel in OCTAVIAN_PRIMARY + OCTAVIAN_SUBMENUS:
        menu_path=ROOT/"boot"/rel
        assert menu_path.is_file(), f"OctavianOS boot menu missing: {rel}"
        actual=timeout(menu_path)
        assert actual==300, f"OctavianOS {rel}: expected 300 seconds, got {actual}"
    for rel in OCTAVIAN_PRIMARY:
        data=(ROOT/"boot"/rel).read_text(encoding="utf-8")
        assert re.search(r"^\s*serial --unit=0 --speed=115200\s*$",data,re.M), f"OctavianOS {rel}: serial console is not initialized"
        assert re.search(r"^\s*terminal_input serial console\s*$",data,re.M), f"OctavianOS {rel}: menu must accept serial and local keyboard input"
# Every interactive boot path that can start a Koronos target must pass the
# matching native ring-3 init ELF; initramfs-only entries are not accepted as
# production Live/Installer/Recovery handoffs.
# Check every menuentry, not just whether a file contains one matching line.
# Any entry that stages a Live/Installer/Recovery payload must also stage the
# matching native ring-3 init ELF in that same menuentry.
MENU_FILES = (
    "iso/grub.cfg", "loader-menu.cfg", "spitfire/spitfire-menu.cfg",
    "jasper/install.cfg", "jasper/live.cfg", "jasper/recovery.cfg",
    "jasper/safe-mode.cfg", "jasper/last-known-good.cfg", "jasper/retro.cfg",
    "installation/services.cfg",
)

def menu_blocks(data):
    for match in re.finditer(r"^\s*menuentry\b", data, re.M):
        opening = data.find("{", match.start())
        if opening < 0:
            continue
        depth = 0
        for end in range(opening, len(data)):
            if data[end] == "{":
                depth += 1
            elif data[end] == "}":
                depth -= 1
                if depth == 0:
                    yield data[match.start():end + 1]
                    break

for rel in MENU_FILES:
    data = (BOOT / rel).read_text(encoding="utf-8")
    for menu in menu_blocks(data):
        required = []
        if "chimera-live-initramfs" in menu:
            required.append("live")
        if "chimera-installation-image" in menu or "chimera-install-image" in menu:
            required.append("installer")
        if "chimera-recovery-initramfs" in menu:
            required.append("recovery")
        for target in required:
            marker = f"target-init-{target}.elf chimera-user-init-elf target={target}"
            assert marker in menu, f"{rel}: menuentry missing native Koronos {target} init module: {menu.splitlines()[0]}"

contract=json.loads((BOOT/"boot-menu-contract.json").read_text())
assert contract["timeouts"]=={"primary_seconds":300,"submenu_seconds":300,"default_entry":"live","policy":"Wait for user input for five minutes on primary and nested boot menus, then select the configured default entry."}
gates=json.loads((SOURCE/"desktop/aurora/gates_menu.json").read_text())
interaction=gates["interaction"]; boot=gates["boot_contract"]
assert interaction["auto_launch_default"] is True
assert interaction["idle_default_timeout_seconds"]==300
assert interaction["menu_remains_open_until_user_action"] is False
assert boot["primary_menu_timeout_seconds"]==300 and boot["submenu_timeout_seconds"]==300
assert boot["default_action"]=="live"
print("PASS: primary and nested menus wait 300 seconds; Gates default action is live.")
