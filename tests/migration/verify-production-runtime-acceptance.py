#!/usr/bin/env python3
"""Fail-closed production ISO gate; CPL3 handoff probes alone are insufficient."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

EVIDENCE = Path("release-evidence/production-runtime-acceptance.json")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_GATES = (
    "cr3_process_context_switching",
    "syscall_abi_and_signal_delivery",
    "vfs_and_real_block_storage",
    "aurora_and_marine_desktop_runtime",
    "installer_disk_write_and_cold_reboot",
    "recovery_repair_postcondition",
    "smp_overlap_on_two_or_more_cpus",
    "native_runtime_for_every_claimed_architecture",
    "same_immutable_iso_six_case_matrix",
)
REQUIRED_CASES = (
    "live_bios", "live_uefi",
    "installer_bios", "installer_uefi",
    "recovery_bios", "recovery_uefi",
)


def fail(message: str) -> int:
    print(f"FAIL: {message}", file=sys.stderr)
    return 1


def main() -> int:
    if not EVIDENCE.is_file():
        return fail(
            f"missing {EVIDENCE}; ring-3 init probes are not production acceptance "
            "and must not authorize a GitHub Release"
        )
    try:
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return fail(f"cannot read production acceptance evidence: {exc}")

    if evidence.get("schema_version") != 1:
        return fail("schema_version must be 1")
    iso_sha = evidence.get("candidate_iso_sha256", "")
    if not isinstance(iso_sha, str) or not SHA256.fullmatch(iso_sha):
        return fail("candidate_iso_sha256 must be a lowercase SHA-256 digest")

    gates = evidence.get("gates")
    if not isinstance(gates, dict):
        return fail("gates object is missing")
    missing = [name for name in REQUIRED_GATES if gates.get(name) is not True]
    if missing:
        return fail("production gates are not proven: " + ", ".join(missing))

    cases = evidence.get("firmware_target_cases")
    if not isinstance(cases, dict):
        return fail("firmware_target_cases object is missing")
    if set(cases) != set(REQUIRED_CASES):
        return fail("firmware_target_cases must contain exactly the six Live/Installer/Recovery × BIOS/UEFI cases")
    for name in REQUIRED_CASES:
        case = cases[name]
        if not isinstance(case, dict):
            return fail(f"{name} evidence must be an object")
        if case.get("passed") is not True:
            return fail(f"{name} did not pass")
        if case.get("iso_sha256") != iso_sha:
            return fail(f"{name} does not use the candidate's same immutable ISO SHA-256")
        for field in ("root_available", "tmp_writable", "target_ready"):
            if case.get(field) is not True:
                return fail(f"{name} is missing verified {field}")
        trace_sha = case.get("trace_sha256", "")
        if not isinstance(trace_sha, str) or not SHA256.fullmatch(trace_sha):
            return fail(f"{name} requires a trace_sha256")

    smp = evidence.get("smp")
    if not isinstance(smp, dict) or int(smp.get("cpu_count", 0)) < 2 or int(smp.get("overlap_intervals", 0)) < 1:
        return fail("SMP evidence must show overlapping execution on at least two CPUs")

    architectures = evidence.get("architectures")
    if not isinstance(architectures, list) or not architectures:
        return fail("architectures must list every claimed native target")
    for item in architectures:
        if not isinstance(item, dict) or item.get("runtime_verified") is not True:
            return fail("every claimed architecture needs native runtime_verified evidence")

    reviewer = evidence.get("reviewed_by")
    if not isinstance(reviewer, str) or not reviewer.strip():
        return fail("reviewed_by is required for production release evidence")

    print("PASS: production runtime evidence covers all required gates and six immutable ISO boots")
    print("Candidate ISO SHA-256:", iso_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
