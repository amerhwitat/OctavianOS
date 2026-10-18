#!/usr/bin/env python3
"""RNN-assisted command candidate ranking; advisory only, never executes unknown commands."""
from __future__ import annotations
import argparse,hashlib,json,re,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
try:
 from tools.cognition.chimera_rnn import RecurrentState
except ModuleNotFoundError:
 sys.path.insert(0,str(Path(__file__).resolve().parent))
 from chimera_rnn import RecurrentState
CATALOG=Path(__file__).resolve().with_name("native-command-candidates.json")
def rank(query,catalog,limit=10):
 tokens=set(re.findall(r"[a-z0-9_+.-]+",query.casefold()));out=[]
 for row in catalog.get("commands",[]):
  name=row.get("name","");nt=set(re.findall(r"[a-z0-9_+.-]+",name.casefold()))
  overlap=len(tokens&nt)/max(1,len(tokens|nt));state=RecurrentState(16)
  h=state.step([overlap,float(row.get("execution_allowed",False)),float(len(name)<=8)])
  score=overlap+0.02*sum(h[:3])/3;out.append((score,row))
 out.sort(key=lambda x:(-x[0],x[1].get("normalized_name","")))
 return [{"name":r["name"],"status":r["status"],"score":round(s,6),"execution_allowed":r["execution_allowed"],"next_step":"native allowlist check" if r["execution_allowed"] else "queue provider discovery and tests; do not execute"} for s,r in out[:limit]]
def queue_unresolved(query,catalog,queue_path):
 normalized=query.strip().casefold()
 exact=next((c for c in catalog.get("commands",[]) if c.get("normalized_name")==normalized),None)
 if exact and exact.get("execution_allowed") is True:return None
 token=(query.strip().split(maxsplit=1)[0] if query.strip() else "")[:128]
 record={"command_token":token,"query_sha256":hashlib.sha256(query.encode("utf-8")).hexdigest(),
  "status":"pending","reason":"not an exact verified native command; provider/implementation evidence required",
  "created_at_utc":datetime.now(timezone.utc).isoformat()}
 queue_path.parent.mkdir(parents=True,exist_ok=True)
 with queue_path.open("a",encoding="utf-8") as stream:stream.write(json.dumps(record,ensure_ascii=False)+"\n")
 return str(queue_path)
def main():
 p=argparse.ArgumentParser();p.add_argument("query");p.add_argument("--limit",type=int,default=10);p.add_argument("--catalog",type=Path,default=CATALOG);p.add_argument("--queue",type=Path,default=Path.home()/".local/state/octavian/command-candidates.jsonl");a=p.parse_args()
 if not 1<=a.limit<=100:raise SystemExit("--limit must be 1..100")
 d=json.loads(a.catalog.read_text(encoding="utf-8"));queued=queue_unresolved(a.query,d,a.queue)
 print(json.dumps({"schema":"OCTAVIAN-RNN-COMMAND-ROUTER-1","engine":"deterministic recurrent-state ranker; not a trained LLM","query":a.query,"results":rank(a.query,d,a.limit),"queued_for_later":bool(queued),"queue_file":queued,"safety":"No command execution, downloads, privilege escalation, or invented implementation claims."},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
