#!/usr/bin/env python3
"""Octavian wrapper around the vendored ISA candidate router and catalog."""
from pathlib import Path
import runpy,sys
ROOT=Path(__file__).resolve().parents[2]
VENDOR=ROOT/"vendor/chimera-ii-os/source"
sys.path.insert(0,str(VENDOR))
sys.argv=[str(VENDOR/"tools/isa/isa_candidate_router.py"),*sys.argv[1:],"--catalog",str(VENDOR/"isa/generated/universal-instruction-catalog.json")]
runpy.run_path(str(VENDOR/"tools/isa/isa_candidate_router.py"),run_name="__main__")
