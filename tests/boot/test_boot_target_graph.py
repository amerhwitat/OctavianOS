#!/usr/bin/env python3
"""Static boot-routing graph tests; these do not replace ISO/QEMU validation."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[2]
CONFIG_ROOTS = [
    ROOT / "boot/iso",
    ROOT / "boot/jasper",
    ROOT / "boot/spitfire",
    ROOT / "boot/installation",
]
VENDORED_CONFIG_ROOTS = [
    ROOT / "vendor/chimera-ii-os/source/boot/iso",
    ROOT / "vendor/chimera-ii-os/source/boot/jasper",
    ROOT / "vendor/chimera-ii-os/source/boot/spitfire",
    ROOT / "vendor/chimera-ii-os/source/boot/installation",
]


def require(condition, message):
    if not condition:
        raise SystemExit("boot target graph regression: " + message)


def read(path):
    return path.read_text(encoding="utf-8")


def main():
    configs = sorted(p for root in CONFIG_ROOTS if root.exists() for p in root.rglob("*.cfg"))
    vendored_configs = sorted(
        p for root in VENDORED_CONFIG_ROOTS if root.exists() for p in root.rglob("*.cfg")
    )
    require(configs, "no boot configuration files found")
    require(vendored_configs, "no vendored Chimera boot configuration files found")
    all_text = "\n".join(read(p) for p in configs)

    # Keep every source menu visible. GRUB's menu timeout is cancelled by a
    # keypress; timeout_style=menu leaves selection to the user instead of
    # hiding the menu behind a countdown. Check imported Chimera menus
    # separately so their configfile edges are not resolved against Octavian.
    for menu in configs + vendored_configs:
        menu_text = read(menu)
        timeouts = re.findall(
            r"^\s*set\s+timeout\s*=\s*([^\s#]+)",
            menu_text,
            re.MULTILINE,
        )
        styles = re.findall(
            r"^\s*set\s+timeout_style\s*=\s*([^\s#]+)",
            menu_text,
            re.MULTILINE,
        )
        require(
            timeouts == ["120"],
            f"{menu.relative_to(ROOT)} must define exactly one 120-second timeout",
        )
        require(
            styles == ["menu"],
            f"{menu.relative_to(ROOT)} must keep its menu visible",
        )

    gates = json.loads(
        read(ROOT / "vendor/chimera-ii-os/source/desktop/aurora/gates_menu.json")
    )
    selection = gates["interaction"]["selection_policy"]
    require(selection.get("wait_for_user_input") is True, "Gates must wait for user input")
    require(selection.get("auto_activate") is False, "Gates must never auto-activate")
    require(selection.get("timeout_seconds") == 300, "Gates timeout must be five minutes")
    require(selection.get("timeout_action") == "remain_open", "Gates timeout must return to the open menu")
    require(
        selection.get("selection_requires_explicit_confirmation") is True,
        "Gates selection must require explicit confirmation",
    )

    # The Octavian main-branch tag workflow can publish an ISO without the
    # same-ISO native acceptance matrix. Keep publication disabled until a
    # production verifier and configured approval are wired into this path.
    release_workflow = read(ROOT / ".github/workflows/release-artifacts.yml")
    publish_match = re.search(
        r"(?ms)^  publish:\s*\n(.*?)(?=^  [A-Za-z0-9_-]+:\s*$|\Z)",
        release_workflow,
    )
    require(publish_match is not None, "release workflow must define an explicit publish job")
    require(
        re.search(r"(?m)^\s+if:\s*false\s*$", publish_match.group(1)) is not None,
        "release publication must remain disabled until native acceptance and approval are implemented",
    )

    # The acceptance log markers contain two '=' delimiters. Both PID
    # fields must be parsed from the third field; field 2 is target metadata,
    # not the numeric PID. This guards the historical ready/ack mismatch.
    acceptance = read(ROOT / ".github/workflows/koronos-userspace-acceptance.yml")
    require(
        'ready_pid="$(printf \'%s\' "$ready_line" | cut -d= -f3)"' in acceptance,
        "ready PID must be extracted from the init_pid field",
    )
    require(
        'ack_pid="$(printf \'%s\' "$ack_line" | cut -d= -f3)"' in acceptance,
        "syscall acknowledgement PID must be extracted from the init_pid field",
    )
    timeout_probe = acceptance.split("\n  timeout-probe:", 1)[1]
    require(
        re.search(
            r'echo "::error::PIT timeout probe blocked by the missing persistent native root filesystem; no PIT deadline evidence was produced\."\s*\n\s+exit 78',
            timeout_probe,
        ) is not None,
        "timeout probe must fail closed when persistent root is unavailable",
    )

    ready_sample = "USERSPACE READY: target=live init_pid=17"
    ack_sample = "USER INIT SYSCALL: target=live init_pid=17"
    require(
        ready_sample.rsplit("=", 1)[-1] == ack_sample.rsplit("=", 1)[-1] == "17",
        "ready and syscall markers must correlate the same nonzero PID",
    )

    builder = read(ROOT / "boot/iso/build-iso.sh")
    require('rm -rf "$ISO_ROOT"' in builder, "native ISO builder must discard stale staged menu files")
    require(
        'cp -f "$ROOT/boot/iso/grub.cfg" "$ISO_ROOT/boot/grub/grub.cfg"' in builder,
        "native ISO builder must stage the canonical visible GRUB menu",
    )
    require(
        'cp -f "$ROOT/$cfg" "$ISO_ROOT/$cfg"' in builder,
        "native ISO builder must stage canonical nested Jasper and Spit Fire menus",
    )

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
    install_block = re.search(r'menuentry[^\n]*--id install\s*\{(.*?)\n\}', grub, re.S).group(1)
    require("multiboot2 /boot/koronos/koronos.elf" in install_block, "GRUB Install must boot Koronos directly")
    require("module2 /install/installer/installation.img chimera-installation-image" in install_block, "GRUB Install must pass the installer image")
    require("chimera-live-initramfs.img" not in install_block, "Install menu must not substitute the live initramfs")

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

    # The vendored Chimera boot menus are part of the shipped native boot path,
    # not merely an inventory snapshot. Require matching CPL3 init payloads for
    # every Multiboot2 entry and preserve the same visible-menu policy upstream.
    vendor_root = ROOT / "vendor/chimera-ii-os/source"

    # The alternate full-ISO builder must stage the same real target init
    # modules and canonical menus as the native ISO path. A GRUB entry without
    # its matching module would otherwise fail only after firmware handoff.
    full_builder = read(vendor_root / "tools/build-full-iso.sh")
    require('TARGET_INIT_DIR="$ROOT/build/koronos/x86_64"' in full_builder,
            "vendored full-ISO builder must use the x86-64 native target output")
    require("for target in live installer recovery; do" in full_builder,
            "vendored full-ISO builder must stage all three production target modules")
    require('test -s "$target_elf"' in full_builder and "readelf -h" in full_builder,
            "vendored full-ISO builder must fail closed on missing/non-executable target modules")
    require('cp -f "$target_elf" "$STAGE/boot/targets/"' in full_builder,
            "vendored full-ISO builder must copy target init ELFs into /boot/targets")
    require('cp -f "$ROOT/boot/iso/grub.cfg" "$STAGE/boot/grub/grub.cfg"' in full_builder,
            "vendored full-ISO builder must stage the canonical GRUB menu")
    require('cp -f "$ROOT/boot/loader-menu.cfg" "$STAGE/boot/loader-menu.cfg"' in full_builder,
            "vendored full-ISO builder must stage the universal loader menu")
    vendor_menu_paths = (
        "boot/iso/grub.cfg",
        "boot/jasper/jasper.cfg",
        "boot/jasper/live.cfg",
        "boot/jasper/install.cfg",
        "boot/jasper/recovery.cfg",
        "boot/jasper/diagnostics.cfg",
        "boot/jasper/retro.cfg",
        "boot/jasper/safe-mode.cfg",
        "boot/jasper/last-known-good.cfg",
        "boot/installation/menu.cfg",
        "boot/spitfire/spitfire-menu.cfg",
    )
    vendor_policy_menu_paths = vendor_menu_paths + (
        "boot/installation/services.cfg",
        "boot/loader-menu.cfg",
    )
    for relative in vendor_policy_menu_paths:
        menu = vendor_root / relative
        require(menu.is_file(), f"vendored native menu is missing: {relative}")
        menu_text = read(menu)
        timeouts = re.findall(r"^\s*set\s+timeout\s*=\s*([^\s#]+)", menu_text, re.MULTILINE)
        styles = re.findall(r"^\s*set\s+timeout_style\s*=\s*([^\s#]+)", menu_text, re.MULTILINE)
        require(timeouts == ["120"], f"vendored {relative} must have exactly one 120-second timeout")
        require(styles == ["menu"], f"vendored {relative} must keep its menu visible")

    # Only the native target menus below are required to stage a target-init
    # ELF. The universal loader and enterprise service selector are menus,
    # but they use their own documented handoff payloads.
    for relative in vendor_menu_paths:
        menu_text = read(vendor_root / relative)
        for block in re.split(r"(?m)(?=^menuentry\b)", menu_text):
            if "multiboot2 " not in block:
                continue
            modules = re.findall(
                r"(?m)^\s*module2\s+/boot/targets/target-init-(live|installer|recovery)\.elf\s+"
                r"chimera-user-init-elf\s+target=(live|installer|recovery)\s+firmware=\$grub_platform\s*$",
                block,
            )
            require(len(modules) == 1, f"vendored {relative} has a Koronos entry without exactly one native init ELF")
            require(modules[0][0] == modules[0][1], f"vendored {relative} has mismatched native init target metadata")

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
