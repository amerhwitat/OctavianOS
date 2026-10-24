#!/usr/bin/env python3
"""Fail-closed production DAPS verifier for a single immutable Koronos ISO.

Evidence is intentionally external to the verifier: this script never creates
readiness markers, treats build success as runtime success, or promotes probe
ISOs to production. See docs/PRODUCTION_DAPS.md for the evidence schema.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

TARGETS = ("live", "installer", "recovery")
FIRMWARES = ("bios", "uefi")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class GateError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GateError(message)


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"cannot read JSON evidence {path}: {exc}") from exc
    require(isinstance(value, dict), f"{path}: top-level JSON must be an object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise GateError(f"cannot hash {path}: {exc}") from exc
    return digest.hexdigest()


def read_trace(root: Path, item: dict, label: str, expected_sha: str) -> str:
    require(isinstance(item, dict), f"{label}: trace record must be an object")
    iso_sha = item.get("iso_sha256")
    require(iso_sha == expected_sha, f"{label}: trace ISO SHA-256 differs from candidate")
    trace_path = (root / str(item.get("log", ""))).resolve()
    require(trace_path.is_relative_to(root.resolve()), f"{label}: trace path escapes evidence root")
    require(trace_path.is_file(), f"{label}: trace file missing: {trace_path}")
    text = trace_path.read_text(encoding="utf-8", errors="replace")
    require("[KRN ] KORONOS READY" in text, f"{label}: kernel-ready marker missing")

    ack = re.findall(
        rf"USER INIT SYSCALL: target={re.escape(label.split('/')[0])} init_pid=([1-9][0-9]*)",
        text,
    )
    ready = re.findall(
        rf"USERSPACE READY: {re.escape(label.split('/')[0])} init pid=([1-9][0-9]*)",
        text,
    )
    require(ack, f"{label}: user-originated CPL3 syscall acknowledgement missing")
    require(ready, f"{label}: userspace readiness marker missing")
    require(ack[-1] == ready[-1], f"{label}: syscall acknowledgement PID and ready PID differ")
    require("USERSPACE SYSCALL RETURNED TO RING3" in text, f"{label}: ring-3 return evidence missing")
    return text


def read_evidence_log(root: Path, relative: object, label: str, markers: tuple[str, ...]) -> str:
    require(isinstance(relative, str) and bool(relative), f"{label}: evidence log reference missing")
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()), f"{label}: evidence log path escapes evidence root")
    require(path.is_file(), f"{label}: evidence log missing: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    for marker in markers:
        require(marker in text, f"{label}: required evidence record missing: {marker}")
    return text


def verify(evidence_path: Path) -> None:
    root = evidence_path.resolve().parent
    evidence = read_json(evidence_path)
    require(evidence.get("schema_version") == 1, "schema_version must be 1")
    iso_path = (root / str(evidence.get("iso", ""))).resolve()
    require(iso_path.is_relative_to(root), "ISO path escapes evidence root")
    require(iso_path.is_file(), "candidate ISO is missing")
    expected_sha = str(evidence.get("iso_sha256", ""))
    require(bool(SHA256_RE.fullmatch(expected_sha)), "iso_sha256 must be lowercase SHA-256")
    actual_sha = sha256_file(iso_path)
    require(actual_sha == expected_sha, f"candidate ISO hash mismatch: expected {expected_sha}, got {actual_sha}")
    with iso_path.open("rb") as stream:
        stream.seek(16 * 2048)
        primary_volume_descriptor = stream.read(7)
    require(primary_volume_descriptor == b"\x01CD001\x01",
            "candidate does not contain an ISO9660 primary volume descriptor at sector 16")

    traces = evidence.get("traces")
    require(isinstance(traces, dict), "traces must be an object")
    trace_text: dict[str, str] = {}
    for target in TARGETS:
        for firmware in FIRMWARES:
            label = f"{target}/{firmware}"
            require(label in traces, f"missing required production trace {label}")
            trace_text[label] = read_trace(root, traces[label], label, expected_sha)

    live = trace_text["live/bios"] + "\n" + trace_text["live/uefi"]
    require("USERSPACE TARGET READY: live component=aurora-session" in live,
            "Live: actual Aurora session readiness missing from both firmware traces")
    require("AURORA READY" in live, "Live: Aurora runtime health marker missing")

    install = evidence.get("installer_persistence")
    require(isinstance(install, dict), "installer_persistence evidence missing")
    require(install.get("passed") is True, "installer persistence/cold reboot not accepted")
    require(install.get("iso_sha256") == expected_sha, "installer persistence evidence references a different ISO")
    require(install.get("write_verified") is True, "installer write postcondition missing")
    require(install.get("cold_reboot_verified") is True, "installed-disk cold reboot not verified")
    require(install.get("installed_system_ready") is True, "installed system readiness not verified")
    read_evidence_log(root, install.get("evidence_log"), "installer persistence", (
        "INSTALL WRITE VERIFIED",
        "INSTALLED DISK COLD REBOOT VERIFIED",
        "INSTALLED SYSTEM READY",
    ))

    recovery = evidence.get("recovery")
    require(isinstance(recovery, dict), "recovery evidence missing")
    require(recovery.get("passed") is True, "recovery repair not accepted")
    require(recovery.get("iso_sha256") == expected_sha, "recovery evidence references a different ISO")
    require(recovery.get("repair_action_executed") is True, "recovery repair action not executed")
    require(recovery.get("postcondition_verified") is True, "recovery repair postcondition not verified")
    read_evidence_log(root, recovery.get("evidence_log"), "recovery repair", (
        "RECOVERY REPAIR EXECUTED",
        "RECOVERY POSTCONDITION VERIFIED",
    ))

    smp = evidence.get("smp")
    require(isinstance(smp, dict), "SMP evidence missing")
    require(smp.get("passed") is True, "AP-backed concurrent SMP not accepted")
    require(smp.get("iso_sha256") == expected_sha, "SMP evidence references a different ISO")
    require(isinstance(smp.get("online_ap_cpus"), list) and len(set(smp["online_ap_cpus"])) >= 2,
            "SMP requires at least two distinct online CPU IDs including AP evidence")
    require(smp.get("overlap_observed") is True, "overlapping execution evidence missing")
    smp_log = read_evidence_log(root, smp.get("per_cpu_trace"), "SMP", ("SMP OVERLAP VERIFIED",))
    observed_cpus = set(re.findall(r"SMP AP ONLINE: cpu=([0-9]+)", smp_log))
    declared_cpus = {str(cpu) for cpu in smp["online_ap_cpus"]}
    require(len(observed_cpus) >= 2, "SMP trace must show at least two AP-online CPU records")
    require(declared_cpus.issubset(observed_cpus), "SMP declared CPU IDs are not all present in per-CPU trace")

    print("PRODUCTION DAPS: PASS")
    print(f"ISO SHA-256: {expected_sha}")
    print("Runtime matrix: Live/Installer/Recovery × BIOS/UEFI: 6/6")
    print("Aurora, installer cold-reboot persistence, recovery postconditions, and AP-backed SMP: PASS")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path,
                        help="JSON evidence manifest; paths are relative to its directory")
    args = parser.parse_args()
    try:
        verify(args.evidence)
    except GateError as exc:
        print(f"PRODUCTION DAPS: BLOCKED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
