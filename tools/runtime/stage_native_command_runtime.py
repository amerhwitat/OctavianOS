#!/usr/bin/env python3
"""Stage Octavian command/ISA routers into installed rootfs and live/recovery initramfs roots."""
from pathlib import Path
import shutil,subprocess,sys

ROOT=Path(__file__).resolve().parents[2]
VENDOR=ROOT/"vendor/chimera-ii-os/source"
TARGETS=[
 VENDOR/"rootfs",
 VENDOR/"build/live-boot/initramfs/root",
]
def copy(src,dst):
 if not src.is_file(): raise SystemExit(f"required runtime input missing: {src}")
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
def stage(target,model_path):
 copy(ROOT/"runtime/commands/native-command-candidates.json",target/"usr/share/octavian/commands/native-command-candidates.json")
 copy(VENDOR/"tools/commands/command_candidate_router.py",target/"usr/share/octavian/commands/command_candidate_router.py")
 copy(VENDOR/"tools/cognition/chimera_rnn.py",target/"usr/share/octavian/commands/chimera_rnn.py")
 copy(VENDOR/"tools/cognition/local_llm.py",target/"usr/share/octavian/commands/local_llm.py")
 copy(VENDOR/"tools/cognition/trainable_rnn_lm.py",target/"usr/share/octavian/commands/trainable_rnn_lm.py")
 copy(model_path,target/"usr/share/octavian/cognition/trained-command-isa-rnn.json")
 copy(ROOT/"runtime/isa/universal-instruction-catalog.json",target/"usr/share/octavian/isa/universal-instruction-catalog.json")
 copy(VENDOR/"tools/isa/isa_candidate_router.py",target/"usr/share/octavian/isa/isa_candidate_router.py")
 copy(VENDOR/"tools/cognition/chimera_rnn.py",target/"usr/share/octavian/isa/chimera_rnn.py")
 copy(VENDOR/"tools/cognition/local_llm.py",target/"usr/share/octavian/isa/local_llm.py")
 copy(VENDOR/"tools/cognition/trainable_rnn_lm.py",target/"usr/share/octavian/isa/trainable_rnn_lm.py")
 bindir=target/"usr/bin";bindir.mkdir(parents=True,exist_ok=True)
 (bindir/"octavian-learn-command").write_text("#!/bin/sh\nset -eu\ncommand -v python3 >/dev/null 2>&1 || { echo \"octavian-learn-command: Python 3 userspace runtime is not installed\" >&2; exit 127; }\nexec python3 /usr/share/octavian/commands/command_candidate_router.py \"$@\" --catalog /usr/share/octavian/commands/native-command-candidates.json\n",encoding="utf-8")
 (bindir/"octavian-learn-isa").write_text("#!/bin/sh\nset -eu\ncommand -v python3 >/dev/null 2>&1 || { echo \"octavian-learn-isa: Python 3 userspace runtime is not installed\" >&2; exit 127; }\nexec python3 /usr/share/octavian/isa/isa_candidate_router.py \"$@\" --catalog /usr/share/octavian/isa/universal-instruction-catalog.json\n",encoding="utf-8")
 (bindir/"octavian-learn-command").chmod(0o755);(bindir/"octavian-learn-isa").chmod(0o755)
def main():
 trainer=VENDOR/"tools/cognition/trainable_rnn_lm.py"
 model=VENDOR/"build/trained-command-isa-rnn.json"
 subprocess.run([sys.executable,str(trainer),"train","--source",str(VENDOR/"isa/isa_database.json"),
  "--source",str(VENDOR/"system/commands/chimera-command-list.json"),"--output",str(model),"--epochs","2","--hidden","12"],check=True)
 for target in TARGETS:stage(target,model)
 print("Trained a bounded character-level RNN from checked-in ISA/command catalogs and staged it with command/ISA candidate routers in installed rootfs and live-initramfs root.")
 print("This is a small trained RNN language model, not an LLM-scale model; it ranks candidates only and cannot enable execution.")
 print("The live-initramfs builder copies this root into the Recovery initramfs; both remain subject to userspace handoff acceptance.")
if __name__=="__main__":main()
