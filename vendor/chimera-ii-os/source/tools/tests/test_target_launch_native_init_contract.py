#!/usr/bin/env python3
"""Source contract for target-matched native init + production payload routing.

This is a structural regression test, not production boot acceptance. Runtime
acceptance still requires the unchanged six-case ISO verifier.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "kernel/core/target_launch.cpp"
text = SOURCE.read_text(encoding="utf-8")

required = [
    "payload_count!=1 || elf_count>1 || !payload",
    "const Target elf_target=parse_target(selected->cmdline);",
    "if (elf_target!=target)",
    "native init ELF target does not match the selected production payload",
    "Selected target-matched native init ELF alongside production root payload",
    "production payload has no separately staged target-matched native init ELF; refusing embedded-init fallback",
    "production rootfs is validated but not mounted; refusing userspace readiness without VFS publication",
]
missing = [item for item in required if item not in text]
if missing:
    raise SystemExit("target-launch native-init contract missing: " + "; ".join(missing))

# The target-specific ELF is an explicit module, not a silently substituted
# candidate. The production payload must independently resolve the target.
if "if (payload_count) {" not in text or "if (elf_count==1)" not in text:
    raise SystemExit("target/payload binding contract missing")

if "chimera_initramfs_find_elf" in text:
    raise SystemExit("target-launch native-init contract missing: embedded CPIO ELF fallback must remain disabled")
print("target-launch native-init contract: PASS (source-level only; not boot acceptance)")
