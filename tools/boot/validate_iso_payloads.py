#!/usr/bin/env python3
"""Validate required payloads in an extracted/staged OctavianOS ISO tree.

This validates packaging contracts only. It does not boot the kernel or prove
that Koronos executes userspace. See docs/BOOT_SEQUENCE_TRACE.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "boot/iso/target-payload-contract.json"
MULTIBOOT2_MAGIC = 0xE85250D6


class ValidationError(RuntimeError):
    pass


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"invalid JSON {path}: {exc}") from exc


def iso_path(root: Path, absolute_path: str) -> Path:
    return root / absolute_path.lstrip("/")


def validate_kernel(path: Path):
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ValidationError(f"cannot read kernel {path}: {exc}") from exc
    if len(data) < 64 or data[:4] != b"\x7fELF":
        raise ValidationError(f"{path}: not a valid ELF image")
    if data[4] != 2 or data[5] != 1:
        raise ValidationError(f"{path}: expected little-endian ELF64 kernel")
    machine = struct.unpack_from("<H", data, 18)[0]
    if machine != 62:
        raise ValidationError(f"{path}: expected x86_64 ELF machine=62, got {machine}")

    scan = data[: min(len(data), 32768)]
    found = False
    for offset in range(0, max(0, len(scan) - 15), 8):
        magic, architecture, header_length, checksum = struct.unpack_from("<IIII", scan, offset)
        if magic != MULTIBOOT2_MAGIC:
            continue
        if architecture != 0:
            raise ValidationError(f"{path}: Multiboot2 header has unsupported architecture field {architecture}")
        if header_length < 16 or offset + header_length > len(data):
            raise ValidationError(f"{path}: malformed Multiboot2 header length {header_length}")
        if (magic + architecture + header_length + checksum) & 0xFFFFFFFF:
            raise ValidationError(f"{path}: Multiboot2 header checksum is invalid")
        found = True
        break
    if not found:
        raise ValidationError(f"{path}: no valid 8-byte-aligned Multiboot2 header in first 32 KiB")
    return {"size": len(data), "sha256": hashlib.sha256(data).hexdigest(), "elf_machine": machine, "multiboot2_header": True}


def validate(root: Path, contract_path: Path, selected_targets: list[str] | None = None,
             expected_hashes_path: Path | None = None):
    contract = load_json(contract_path)
    if contract.get("status") != "staging-contract-only":
        raise ValidationError("target payload contract must not claim build/runtime success")
    kernel_contract = contract.get("kernel", {})
    kernel_file = iso_path(root, kernel_contract.get("path", "/boot/koronos/koronos.elf"))
    if not kernel_file.is_file() or kernel_file.stat().st_size == 0:
        raise ValidationError(f"required kernel is missing or empty: {kernel_contract.get('path')}")
    kernel_info = validate_kernel(kernel_file)

    targets = contract.get("targets", {})
    chosen = selected_targets or sorted(targets)
    unknown = sorted(set(chosen) - set(targets))
    if unknown:
        raise ValidationError("unknown target(s): " + ", ".join(unknown))

    required_paths = {kernel_contract.get("path", "/boot/koronos/koronos.elf")}
    for target in chosen:
        required_paths.update(targets[target].get("required", []))

    # A payload may be required by multiple targets; validate each path once.
    payload_report = {}
    for path in sorted(required_paths):
        full = iso_path(root, path)
        if not full.is_file() or full.stat().st_size == 0:
            raise ValidationError(f"required payload is missing or empty for target(s) {', '.join(t for t in chosen if path in targets[t].get('required', [])) or 'kernel'}: {path}")
        digest = hashlib.sha256(full.read_bytes()).hexdigest()
        payload_report[path] = {"size": full.stat().st_size, "sha256": digest}
        if path.endswith(".json"):
            parsed = load_json(full)
            if path.endswith("desktop-sessions.json"):
                ids = {item.get("id") for item in parsed.get("sessions", [])}
                if not {"aurora", "marine"}.issubset(ids):
                    raise ValidationError(f"{path}: must define Aurora and Marine session IDs")

    # Optional targets must be fully absent or fully staged; partial installs are errors.
    for target, paths in contract.get("optional_targets", {}).items():
        present = [iso_path(root, path).is_file() and iso_path(root, path).stat().st_size > 0 for path in paths]
        if any(present) and not all(present):
            raise ValidationError(f"optional target {target} is only partially staged")

    if expected_hashes_path:
        expected = load_json(expected_hashes_path)
        for path, digest in expected.items():
            if path not in payload_report:
                full = iso_path(root, path)
                if not full.is_file():
                    raise ValidationError(f"hash manifest references missing payload {path}")
                payload_report[path] = {"size": full.stat().st_size, "sha256": hashlib.sha256(full.read_bytes()).hexdigest()}
            if payload_report[path]["sha256"].lower() != str(digest).lower():
                raise ValidationError(f"SHA-256 mismatch for {path}")

    return {
        "status": "payload-contract-passed",
        "scope": "staged ISO payload validation only; no boot/runtime claim",
        "targets_checked": chosen,
        "kernel": {"path": kernel_contract.get("path"), **kernel_info},
        "payloads": payload_report,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="root directory of extracted/staged ISO contents")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT, help="target-payload-contract.json")
    parser.add_argument("--targets", nargs="+", help="subset of target IDs; default checks every required target")
    parser.add_argument("--sha256-manifest", type=Path, help="optional JSON map of ISO absolute paths to expected SHA-256")
    parser.add_argument("--report", type=Path, help="optional path to write a JSON validation report")
    args = parser.parse_args()

    try:
        result = validate(args.root, args.contract, args.targets, args.sha256_manifest)
    except ValidationError as exc:
        print(f"OctavianOS ISO payload validation FAILED: {exc}", file=sys.stderr)
        return 1
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
