#!/usr/bin/env python3
"""Validate evidence contract only; not a boot test."""
import json
from pathlib import Path
d=json.loads((Path(__file__).resolve().parent/"boot"/"six_case_acceptance_contract.json").read_text())
assert d["schema"]=="CHM-OS-PRODUCTION-SIX-CASE-1" and d["status"]=="contract-only"
assert len(d["cases"])==6
assert {c["target"] for c in d["cases"]}=={"live","installer","recovery"}
assert {c["firmware"] for c in d["cases"]}=={"bios","uefi"}
assert len({c["id"] for c in d["cases"]})==6
for c in d["cases"]:
 assert c["status"]=="NOT_RUN"
 assert c["evidence"]["init_pid"] is None and c["evidence"]["syscall_cpl"] is None
print("PASS: contract schema valid; six runtime cases remain NOT_RUN")
