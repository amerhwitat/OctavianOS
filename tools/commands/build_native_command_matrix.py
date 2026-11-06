#!/usr/bin/env python3
"""Cross-build the real Chimera native multicall command for supported Linux ABIs.

A successful cross-build proves only that a target ELF was produced and its
machine field matches. It does not prove that Koronos boots or runs on that ISA.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

TARGETS = {
    "x86_64": {"compiler": "cc", "machine": "Advanced Micro Devices X86-64", "elf_machine": 62},
    "aarch64": {"compiler": "aarch64-linux-gnu-gcc", "machine": "AArch64", "elf_machine": 183},
    "riscv64": {"compiler": "riscv64-linux-gnu-gcc", "machine": "RISC-V", "elf_machine": 243},
}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def machine_from_readelf(readelf: str, binary: Path) -> str:
    out = subprocess.run([readelf, "-h", str(binary)], check=True, text=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
    for line in out.splitlines():
        if line.strip().startswith("Machine:"):
            return line.split(":", 1)[1].strip()
    raise RuntimeError(f"ELF machine field missing: {binary}")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--policy", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--require-all", action="store_true")
    args = ap.parse_args()
    policy = json.loads(args.policy.read_text(encoding="utf-8"))
    aliases = policy["native_build"]["multicall_aliases"]
    if not args.source.is_file():
        raise SystemExit(f"native command source not found: {args.source}")
    readelf = shutil.which("readelf")
    if not readelf:
        raise SystemExit("readelf is required to validate target ELF machine fields")
    args.output.mkdir(parents=True, exist_ok=True)
    rows = []
    failures = []
    for target, spec in TARGETS.items():
        compiler = shutil.which(spec["compiler"])
        row = {"target": target, "compiler": spec["compiler"],
               "binary_status": "not-built", "runtime_status": "not-tested",
               "aliases": aliases}
        if not compiler:
            row["reason"] = "target compiler unavailable"
            failures.append(target)
            rows.append(row)
            continue
        outdir = args.output / target
        outdir.mkdir(parents=True, exist_ok=True)
        binary = outdir / "chimera-cmd"
        cmd = [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
               str(args.source), "-o", str(binary)]
        proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode:
            row["reason"] = "compiler failed"
            row["compiler_stderr"] = proc.stderr[-4000:]
            failures.append(target)
            rows.append(row)
            continue
        machine = machine_from_readelf(readelf, binary)
        expected = spec["machine"]
        if expected.casefold() not in machine.casefold():
            row["reason"] = f"ELF machine mismatch: expected {expected}, got {machine}"
            failures.append(target)
            rows.append(row)
            continue
        for name in aliases:
            link = outdir / name
            if link.exists() or link.is_symlink():
                link.unlink()
            link.symlink_to("chimera-cmd")
        row.update({"binary_status": "cross-compiled-and-elf-machine-validated",
                    "elf_machine": machine, "elf_machine_id": spec["elf_machine"],
                    "binary": str(binary.relative_to(args.output)),
                    "sha256": sha256(binary),
                    "runtime_status": "not-tested-cross-build-only"})
        rows.append(row)
    manifest = {
        "schema": "CHM-NATIVE-COMMAND-ISA-BUILD-1",
        "source": str(args.source),
        "policy": "Only compiled outputs with a verified ELF machine field are marked built. Cross-compilation is not native runtime acceptance.",
        "native_command_count": len(aliases),
        "target_count": len(TARGETS),
        "targets": rows,
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"built": sum(r["binary_status"] == "cross-compiled-and-elf-machine-validated" for r in rows),
                      "targets": len(rows), "failures": failures}, sort_keys=True))
    if args.require_all and failures:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
