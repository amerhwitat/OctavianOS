#!/usr/bin/env python3
"""Wire the ring-3 USER_INIT_ELF probe modules into the GRUB menu.

Koronos only performs the protected ring-3 handoff when exactly one
Multiboot2 module is classified as CHIMERA_MODULE_USER_INIT_ELF and its
cmdline selects exactly one target=live|installer|recovery token.
This script inserts that module line into each menu entry, idempotently.
"""
import re
import sys
from pathlib import Path

CFG = Path(__file__).resolve().parent / "grub.cfg"

# menuentry id -> target
TARGETS = {
    "aurora-live": "live",
    "normal": "live",
    "live-progress": "live",
    "services": "live",
    "safe-mode": "live",
    "last-known-good": "live",
    "retro": "live",
    "mobile": "live",
    "spitfire": "live",
    "install": "installer",
    "recovery": "recovery",
    "diagnostics": "recovery",
}

text = CFG.read_text()
lines = text.splitlines()

out = []
current_id = None
depth = 0
inserted = 0

id_re = re.compile(r'^\s*menuentry\s+.*--id\s+([A-Za-z0-9_.-]+)')

for line in lines:
    m = id_re.match(line)
    if m:
        current_id = m.group(1)
        depth = 0
    if current_id:
        depth += line.count("{") - line.count("}")
    # Insert just before the closing brace of the menu entry, after `boot`
    if current_id and depth == 0 and line.strip() == "}":
        target = TARGETS.get(current_id)
        if target:
            mod = (f"  module2 /boot/chimera/elf/user-init-{target}.elf "
                   f"chimera-user-init-elf target={target}")
            # idempotency: only insert if not already present in this block
            block = "\n".join(out)
            last_open = block.rfind("menuentry")
            if mod.strip() not in block[last_open:]:
                out.append(mod)
                inserted += 1
        current_id = None
    out.append(line)

CFG.write_text("\n".join(out) + "\n")
print(f"inserted {inserted} user-init module lines")
