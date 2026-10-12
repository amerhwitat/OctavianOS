#!/usr/bin/env python3
"""Static boot-routing graph tests; these do not replace ISO/QEMU validation."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[2]
CONFIG_ROOTS = [ROOT / "boot/iso", ROOT / "boot/jasper", ROOT / "boot/spitfire", ROOT / "boot/installation"]


def require(condition, message):
    if not condition:
        raise SystemExit("boot target graph regression: " + message)


def read(path):
    return path.read_text(encoding="utf-8")


def main():
    configs = sorted(p for root in CONFIG_ROOTS if root.exists() for p in root.rglob("*.cfg"))
    require(configs, "no boot configuration files found")
    all_text = "\n".join(read(p) for p in configs)

    # Every absolute configfile edge must resolve to a tracked source config.
    targets = re.findall(r"\bconfigfile\s+(/boot/[^\s;]+)", all_text)
    require(targets, "no configfile edges discovered")
    missing = sorted({target for target in targets if not (ROOT / target.lstrip("/")).is_file()})
    require(not missing, "configfile edges point to missing tracked configs: " + ", ".join(missing))

    grub = read(ROOT / "boot/iso/grub.cfg")
    jasper = read(ROOT / "boot/jasper/jasper.cfg")
    live = read(ROOT / "boot/jasper/live.cfg")
    installer = read(ROOT / "boot/jasper/install.cfg")
    recovery = read(ROOT / "boot/jasper/recovery.cfg")
    diagnostics = read(ROOT / "boot/jasper/diagnostics.cfg")
    safe = read(ROOT / "boot/jasper/safe.cfg")
    retro = read(ROOT / "boot/jasper/retro.cfg")
    spitfire = read(ROOT / "boot/spitfire/spitfire-menu.cfg")

    for menu_id in ("aurora-live", "marine-live", "install", "normal", "recovery", "diagnostics", "safe-mode", "last-known-good", "retro", "spitfire", "jasper"):
        require(re.search(r"--id\s+" + re.escape(menu_id) + r"\b", grub), f"top-level menu ID missing: {menu_id}")

    require("configfile /boot/jasper/jasper.cfg" in grub, "normal/select-target entry must route to Jasper, not masquerade as installed-system boot")
    require("chm.desktop=aurora" in grub and "chm.desktop=marine" in grub, "top-level Aurora and Marine desktop profiles are not distinct")
    aurora_block = re.search(r'menuentry[^\n]*--id live-aurora\s*\{(.*?)\n\}', live, re.S)
    marine_block = re.search(r'menuentry[^\n]*--id live-marine\s*\{(.*?)\n\}', live, re.S)
    require(aurora_block and "/boot/live/desktop-sessions.json" in aurora_block.group(1), "Aurora session manifest must be required and passed to Koronos")
    require(marine_block and "/boot/live/desktop-sessions.json" in marine_block.group(1), "Marine session manifest must be required and passed to Koronos")
    require("module2 /boot/live/desktop-sessions.json octavian-desktop-sessions" in grub, "top-level Live entries do not pass desktop-selection contract")
    require("configfile /boot/jasper/install.cfg" in grub, "GRUB Install must route to the dedicated Jasper installer")
    require("chimera-live-initramfs.img" not in re.search(r'menuentry[^\n]*--id install\s*\{(.*?)\n\}', grub, re.S).group(1), "Install menu must not substitute the live initramfs")

    for item in ("chm.desktop=aurora", "chm.desktop=marine"):
        require(item in live, f"Live menu is missing desktop profile {item}")
    require("configfile /boot/jasper/safe.cfg" in jasper, "Jasper safe mode must route to direct safe target")
    require("chm.mode=safe chm.graphics=basic" in safe, "safe target must explicitly request basic graphics mode")
    require("module2 /install/installer/installation.img chimera-installation-image" in installer, "native installer image not passed to Koronos")
    for path in ("installation-manifest.json", "installer-contract.json", "installation_phases.json", "installer_profiles.json"):
        require(path in installer, f"installer contract is missing {path}")
    require("chm.mode=recovery" in recovery, "recovery mode is not explicitly requested")
    require("chm.mode=diagnostics" in diagnostics, "diagnostics mode is not explicitly requested")
    require("No rollback snapshot is staged" in grub, "missing last-known-good snapshot must fail closed")
    require("not present in this ISO" in retro, "missing retro payload must be reported rather than booting an unrelated payload")
    require("configfile /boot/jasper/jasper.cfg" in spitfire, "Spit Fire must offer Jasper as the canonical target manager")

    payload_contract = json.loads(read(ROOT / "boot/iso/target-payload-contract.json"))
    require(payload_contract["status"] == "staging-contract-only", "payload manifest must not claim ISO assets are built")
    require(payload_contract["targets"]["live-aurora"]["desktop"] == "chm.desktop=aurora", "Aurora payload contract is inconsistent")
    require(payload_contract["targets"]["live-marine"]["desktop"] == "chm.desktop=marine", "Marine payload contract is inconsistent")
    require("/install/installer/installation.img" in payload_contract["targets"]["installer"]["required"], "installer image is absent from staging contract")
    require("/boot/recovery/chimera-recovery-initramfs.img" in payload_contract["targets"]["recovery"]["required"], "recovery payload is absent from staging contract")

    sessions = json.loads(read(ROOT / "boot/live/desktop-sessions.json"))
    session_ids = {s["id"] for s in sessions["sessions"]}
    require(session_ids == {"aurora", "marine"}, "desktop selection contract must define exactly Aurora and Marine")
    require(sessions["status"] == "selection-contract-only", "desktop manifest must not claim native launch readiness")

    print(f"boot target graph static contract: PASS ({len(configs)} configs, {len(set(targets))} configfile edges)")
    print("This is source-level validation only; ISO payload existence, GRUB runtime, Koronos handoff, and desktop readiness require build/QEMU tests.")


if __name__ == "__main__":
    main()
