#!/usr/bin/env python3
"""Stage Octavian's own command/ISA candidate catalogs and advisory RNN tools in rootfs."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[2]
VENDOR=ROOT/"vendor/chimera-ii-os/source"
ROOTFS=VENDOR/"rootfs"
def copy(src,dst):
 if not src.is_file(): raise SystemExit(f"required runtime input missing: {src}")
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
def main():
 copy(ROOT/"runtime/commands/native-command-candidates.json",ROOTFS/"usr/share/octavian/commands/native-command-candidates.json")
 copy(VENDOR/"tools/commands/command_candidate_router.py",ROOTFS/"usr/share/octavian/commands/command_candidate_router.py")
 copy(VENDOR/"tools/cognition/chimera_rnn.py",ROOTFS/"usr/share/octavian/commands/chimera_rnn.py")
 copy(ROOT/"runtime/isa/universal-instruction-catalog.json",ROOTFS/"usr/share/octavian/isa/universal-instruction-catalog.json")
 copy(VENDOR/"tools/isa/isa_candidate_router.py",ROOTFS/"usr/share/octavian/isa/isa_candidate_router.py")
 copy(VENDOR/"tools/cognition/chimera_rnn.py",ROOTFS/"usr/share/octavian/isa/chimera_rnn.py")
 bindir=ROOTFS/"usr/bin";bindir.mkdir(parents=True,exist_ok=True)
 (bindir/"octavian-learn-command").write_text("#!/bin/sh\nset -eu\nexec python3 /usr/share/octavian/commands/command_candidate_router.py \"$@\" --catalog /usr/share/octavian/commands/native-command-candidates.json\n",encoding="utf-8")
 (bindir/"octavian-learn-isa").write_text("#!/bin/sh\nset -eu\nexec python3 /usr/share/octavian/isa/isa_candidate_router.py \"$@\" --catalog /usr/share/octavian/isa/universal-instruction-catalog.json\n",encoding="utf-8")
 (bindir/"octavian-learn-command").chmod(0o755);(bindir/"octavian-learn-isa").chmod(0o755)
 print("Staged Octavian command candidates, ISA catalog, and advisory RNN routers.")
if __name__=="__main__":main()
