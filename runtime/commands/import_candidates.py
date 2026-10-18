#!/usr/bin/env python3
"""Generate Octavian's own command-candidate registry from vendored upstream catalogs."""
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
VENDOR=ROOT/"vendor/chimera-ii-os/source"
IMPORTER=VENDOR/"tools/commands/import_command_candidates.py"
OUT=ROOT/"runtime/commands/native-command-candidates.json"
def main():
 if not IMPORTER.is_file(): raise SystemExit("vendored command importer missing; sync verified Chimera source first")
 subprocess.run([sys.executable,str(IMPORTER),"--output",str(OUT)],cwd=VENDOR,check=True)
if __name__=="__main__":main()
