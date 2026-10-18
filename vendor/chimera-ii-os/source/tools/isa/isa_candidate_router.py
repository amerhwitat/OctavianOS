#!/usr/bin/env python3
"""RNN-assisted ISA retrieval; catalog rows never imply executable support."""
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
try:
 from tools.cognition.chimera_rnn import RecurrentState
except ModuleNotFoundError:
 sys.path.insert(0,str(Path(__file__).resolve().parent))
 from chimera_rnn import RecurrentState
DEFAULT=Path(__file__).resolve().with_name("universal-instruction-catalog.json")
def tokens(value):return set(re.findall(r"[a-z0-9_+.-]+",str(value).casefold()))
def rank(query,catalog,limit=10):
 q=tokens(query);out=[]
 for row in catalog.get("instructions",[]):
  t=tokens(" ".join(str(row.get(k,"")) for k in ("architecture","mnemonic","form_id","source_ref","extensions")))
  overlap=len(q&t)/max(1,len(q|t));state=RecurrentState(24)
  h=state.step([overlap,float(row.get("encoding_status")=="sourced-mask-verified"),float(row.get("execution_status")=="conformance-tested")])
  score=overlap+0.02*sum(h[:4])/4;out.append((score,row))
 out.sort(key=lambda x:(-x[0],x[1].get("architecture",""),x[1].get("mnemonic",""),x[1].get("form_id","")))
 return [{"architecture":r.get("architecture"),"mnemonic":r.get("mnemonic"),"form_id":r.get("form_id"),"encoding_status":r.get("encoding_status"),"execution_status":r.get("execution_status"),"source_ref":r.get("source_ref"),"score":round(s,6),"execution_allowed":False,"next_step":"verify architecture manual and conformance vectors before implementation"} for s,r in out[:limit]]
def main():
 p=argparse.ArgumentParser();p.add_argument("query");p.add_argument("--limit",type=int,default=10);p.add_argument("--catalog",type=Path,default=DEFAULT);a=p.parse_args()
 if not 1<=a.limit<=100:raise SystemExit("--limit must be 1..100")
 d=json.loads(a.catalog.read_text(encoding="utf-8"));results=rank(a.query,d,a.limit)
 print(json.dumps({"schema":"OCTAVIAN-RNN-ISA-CANDIDATE-ROUTER-1","engine":"deterministic recurrent-state ranking; not a trained LLM","query":a.query,"result_count":len(results),"results":results,"safety":"Advisory only; no opcode, semantic, native mapping, or conformance fact is invented."},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
