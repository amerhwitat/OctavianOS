#!/usr/bin/env python3
"""Train a small auditable RNN language model on Octavian's imported catalogs."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
VENDOR=ROOT/"vendor/chimera-ii-os/source"
sys.path.insert(0,str(VENDOR))
from tools.cognition.trainable_rnn_lm import CharRNN

def corpus_from(commands_path,isa_path):
 commands=json.loads(commands_path.read_text(encoding="utf-8"))
 isa=json.loads(isa_path.read_text(encoding="utf-8"))
 command_rows=[];isa_rows=[]
 for c in commands.get("commands",[]):
  command_rows.append("command "+str(c.get("name",""))+" status "+str(c.get("status",""))+" provider "+str(c.get("provider",""))+" target "+str(c.get("target","")))
 for ins in isa.get("instructions",[]):
  isa_rows.append("instruction "+str(ins.get("architecture",""))+" "+str(ins.get("mnemonic",""))+" form "+str(ins.get("form_id",""))+" encoding "+str(ins.get("encoding_status",""))+" execution "+str(ins.get("execution_status","")))
 def sample(rows,limit=200):
  rows=[r[:160] for r in rows if len(r.strip())>=3]
  if len(rows)<=limit:return rows
  return [rows[(i*(len(rows)-1))//(limit-1)] for i in range(limit)]
 # Balanced, deterministic sample keeps CI training bounded while representing
 # the full imported catalogs rather than training only on command rows.
 return sample(command_rows)+sample(isa_rows),commands,isa

def main():
 import argparse
 p=argparse.ArgumentParser()
 p.add_argument("--commands",type=Path,default=ROOT/"runtime/commands/native-command-candidates.json")
 p.add_argument("--isa",type=Path,default=ROOT/"runtime/isa/universal-instruction-catalog.json")
 p.add_argument("--output",type=Path,default=ROOT/"runtime/cognition/trained-command-isa-rnn.json")
 p.add_argument("--epochs",type=int,default=2)
 p.add_argument("--hidden",type=int,default=8)
 a=p.parse_args()
 rows,commands,isa=corpus_from(a.commands,a.isa)
 if len(rows)<100: raise SystemExit(f"refusing to train on too-small catalog corpus: {len(rows)} rows")
 chars=sorted(set("".join(rows)+" \n"))
 model=CharRNN(chars,hidden=a.hidden,seed=7)
 losses=model.train(rows,epochs=a.epochs,learning_rate=0.025)
 digest=hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()
 metadata={"training_source":"Octavian command candidate catalog + universal ISA catalog","training_sequences":len(rows),
  "command_rows":commands.get("counts",{}).get("total",len(commands.get("commands",[]))),
  "isa_rows":len(isa.get("instructions",[])),"corpus_sha256":digest,"epochs":len(losses),
  "loss_first":losses[0],"loss_last":losses[-1],"seed":7,"hidden_size":a.hidden,
  "model_scope":"small trained character-level RNN language model; not an LLM-scale model; advisory ranking only"}
 a.output.parent.mkdir(parents=True,exist_ok=True)
 model.save(a.output,metadata)
 report={"schema":"OCTAVIAN-RUNTIME-COGNITION-CAPABILITIES-1","status":"staged-host-smoke-only",
  "model_type":"trained-character-level-vanilla-RNN","model_file":a.output.name,"model_trained":True,
  "training_sequences":len(rows),"command_rows":metadata["command_rows"],"isa_rows":metadata["isa_rows"],
  "epochs":len(losses),"loss_first":losses[0],"loss_last":losses[-1],"corpus_sha256":digest,
  "host_router_smoke_tested_in_ci":False,"in_os_execution_verified":False,"python3_required":True,
  "kernel_userspace_ready_verified":False,
  "blockers":["Koronos must provide a verified user process address space and ring-3 transition.",
   "The target userspace must provide Python 3 or a native port of the RNN scorer.",
   "Live, Installer, and Recovery each need an actual nonzero init PID readiness marker."],
  "safety":"Advisory scoring only; model output never authorizes command execution or ISA conformance."}
 (a.output.parent/"runtime-capabilities.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
 loaded=CharRNN.load(a.output)
 if abs(loaded.score(rows[0])-model.score(rows[0]))>1e-8: raise SystemExit("trained model round-trip validation failed")
 print(json.dumps({"status":"trained-and-roundtrip-validated","model_type":"trained-character-level-vanilla-RNN",
  "training_sequences":len(rows),"command_rows":metadata["command_rows"],"isa_rows":metadata["isa_rows"],
  "vocabulary":len(chars),"hidden_size":a.hidden,"epochs":len(losses),"loss_first":losses[0],"loss_last":losses[-1],
  "corpus_sha256":digest,"model":str(a.output),"capabilities_report":str(a.output.parent/"runtime-capabilities.json")},ensure_ascii=False))
if __name__=="__main__":main()
