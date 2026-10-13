#!/usr/bin/env python3
"""OctavianOS entry point for the vendored Chimera source-backed ISA refresh."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
VENDORED = ROOT / "vendor/chimera-ii-os/source/tools/isa/refresh_isa_catalog.py"
if not VENDORED.is_file():
    raise SystemExit(f"vendored ISA refresh tool missing: {VENDORED}")
raise SystemExit(subprocess.call([sys.executable, str(VENDORED), *sys.argv[1:]], cwd=VENDORED.parents[2]))
