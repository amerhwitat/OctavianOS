#!/usr/bin/env python3
"""Octavian runtime bridge to the vendored deterministic RNN command candidate ranker."""
from pathlib import Path
import runpy,sys
ROOT=Path(__file__).resolve().parents[2]
VENDOR=ROOT/"vendor/chimera-ii-os/source"
sys.path.insert(0,str(VENDOR))
sys.argv=[str(VENDOR/"tools/commands/command_candidate_router.py"),*sys.argv[1:],"--catalog",str(ROOT/"runtime/commands/native-command-candidates.json")]
runpy.run_path(str(VENDOR/"tools/commands/command_candidate_router.py"),run_name="__main__")
