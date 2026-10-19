#!/usr/bin/env python3
"""Validate six-case evidence schema only; this is not an ISO/QEMU boot test."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[2]
d=json.loads((root/"tests/boot/six_case_acceptance_contract.json").read_text())
assert d["schema"]=="CHM-OS-PRODUCTION-SIX-CASE-1" and d["status"]=="contract-only"
assert len(d["cases"])==6
assert {c["target"] for c in d["cases"]}=={"live","installer","recovery"}
assert {c["firmware"] for c in d["cases"]}=={"bios","uefi"}
assert len({c["id"] for c in d["cases"]})==6
for c in d["cases"]:
    assert c["status"]=="NOT_RUN", "contract must not predeclare runtime PASS"
    e=c["evidence"]
    for k in ("iso_sha256","kernel_sha","qemu_version","init_pid","syscall_cpl","syscall_log","ready_log","artifact_url"): assert k in e
    assert e["init_pid"] is None and e["syscall_cpl"] is None
assert "USER INIT SYSCALL" in d["required_events"]["syscall"]
assert "USERSPACE READY" in d["required_events"]["ready"]
assert "CPL3" in d["required_events"]["provenance"]
print("PASS: six-case contract valid; runtime cases remain NOT_RUN.")
