#!/usr/bin/env python3
"""Regression test for the vendored native Koronos release build gate."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
script = (root / "build-chimera-iso.sh").read_text(encoding="utf-8")
assert 'if [[ "$RELEASE_BUILD" == 1 && "$RUN_NATIVE_SIX_CASE_DIAGNOSTICS" != 1 ]]' in script
assert 'Release mode requires QEMU and OVMF for all six same-ISO cases.' in script
assert 'Release mode requires a matching OVMF_CODE/OVMF_VARS pair.' in script
print("Vendored ISO builder fail-closed six-case release gate: PASS")
