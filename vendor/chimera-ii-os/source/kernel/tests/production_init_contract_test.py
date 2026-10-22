#!/usr/bin/env python3
"""Source contract: production userspace requires a separate target-matched ELF."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "core/target_launch.cpp").read_text(encoding="utf-8")

def fail(message):
    print("PRODUCTION INIT CONTRACT FAIL: " + message, file=sys.stderr)
    return 1

if "production payload has no separately staged target-matched native init ELF" not in source:
    raise SystemExit(fail("missing native init ELF must fail closed"))
if "chimera_initramfs_find_elf" in source:
    raise SystemExit(fail("production launch must not fall back to executing an ELF found inside CPIO"))
if "parse_target(selected->cmdline)" not in source or "elf_target!=target" not in source:
    raise SystemExit(fail("native init target must match independently classified payload"))
print("PRODUCTION INIT CONTRACT PASS: separate target-matched ELF required; embedded fallback rejected")
