#!/usr/bin/env python3
"""Fail closed when a GRUB Multiboot2 entry omits or mismatches its target payload."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
BOOT = ROOT / "vendor/chimera-ii-os/source/boot"
TARGET_RE = re.compile(r"(?:^|\\s)chimera\\.target=(live|installer|recovery)(?=\\s|$)")
failures = []
checked = 0

for path in sorted(BOOT.rglob("*.cfg")):
    lines = path.read_text(encoding="utf-8").splitlines()
    starts = [i for i, line in enumerate(lines) if line.lstrip().startswith("menuentry ")]
    for pos, start in enumerate(starts):
        end = starts[pos + 1] if pos + 1 < len(starts) else len(lines)
        block = lines[start:end]
        commands = [line for line in block if re.search(r"\\bmultiboot2\\s+", line)]
        if not commands:
            continue
        checked += 1
        targets = []
        for command in commands:
            tokens = TARGET_RE.findall(command)
            all_selectors = re.findall(r"chimera\\.target=", command)
            if len(tokens) != 1 or len(all_selectors) != 1:
                failures.append(f"{path.relative_to(ROOT)}:{start + 1}: each multiboot2 command must contain exactly one valid chimera.target selector")
            else:
                targets.append(tokens[0])
        if len(set(targets)) > 1:
            failures.append(f"{path.relative_to(ROOT)}:{start + 1}: multiboot2 commands in one menu entry disagree on target")
        if not targets:
            continue
        target = targets[0]
        text = "\\n".join(block)
        if target == "live" and not re.search(r"live-initramfs(?:\\.img)?", text):
            failures.append(f"{path.relative_to(ROOT)}:{start + 1}: live target has no live initramfs module")
        elif target == "installer" and not re.search(r"(?:chimera-installation-image|chimera-install-image|/installation\\.img)", text):
            failures.append(f"{path.relative_to(ROOT)}:{start + 1}: installer target has no installation image module")
        elif target == "recovery" and not re.search(r"chimera-recovery-initramfs|recovery-initramfs\\.img", text):
            failures.append(f"{path.relative_to(ROOT)}:{start + 1}: recovery target has no recovery initramfs module")

if failures:
    print("\\n".join(failures), file=sys.stderr)
    sys.exit(1)
print(f"GRUB target-routing contract: PASS ({checked} Multiboot2 menu entries checked)")
