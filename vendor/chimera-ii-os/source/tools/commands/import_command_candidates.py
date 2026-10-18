#!/usr/bin/env python3
"""Import command names as safe native/cross-OS candidates; never promotes catalog rows to executables."""
from __future__ import annotations
import argparse, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE=ROOT/"system/commands/chimera-command-list.json"
DEFAULT_SS64=ROOT/"system/commands/ss64-command-catalog.json"
DEFAULT_ARABIC=ROOT/"system/commands/ss64-command-catalog.ar.json"
DEFAULT_OUT=ROOT/"system/commands/native-command-candidates.json"
NATIVE={"pwd","echo","ls","cp","mv","touch","mkdir","rm","cat","clear","whoami","hostname","date","true","false"}
COMMON=set("pwd echo ls cp mv touch mkdir rm cat clear whoami hostname date true false printf grep find head tail sort wc cut tr env uname id ps kill chmod chown df du mount umount tar gzip sha256sum curl wget git python3 sh bash test help man history cd exit read export alias which command".split())
def load(p):
 try: return json.loads(p.read_text(encoding="utf-8"))
 except (OSError,json.JSONDecodeError): return {}
def build(source,ss64,arabic):
 rows={}
 def add(name,platform,url=None):
  if not name or not str(name).strip(): return
  name=str(name).strip(); key=name.casefold()
  row=rows.setdefault(key,{"name":name,"platforms":[],"source_urls":[]})
  if platform not in row["platforms"]: row["platforms"].append(platform)
  if url and url not in row["source_urls"]: row["source_urls"].append(url)
 for platform,items in source.items():
  if isinstance(items,list):
   for x in items:
    if isinstance(x,str): add(x,platform)
    elif isinstance(x,dict) and x.get("name"): add(x["name"],platform,x.get("source"))
 for platform,data in ss64.get("platforms",{}).items():
  for x in data.get("commands",[]):
   if isinstance(x,dict) and x.get("name"): add(x["name"],platform,x.get("source"))
 for name in COMMON: add(name,"common-command-candidate")
 for name in NATIVE: add(name,"octavian-native-implemented")
 labels=arabic.get("commands",{})
 for key,value in labels.items():
  name=value.get("name",key) if isinstance(value,dict) else key
  add(name,"arabic-command-catalog")
 commands=[]
 for key,row in sorted(rows.items()):
  is_native=key in NATIVE; label=labels.get(key)
  commands.append({"name":row["name"],"normalized_name":key,"platforms":sorted(row["platforms"]),
   "status":"native-implemented" if is_native else "candidate-only",
   "dispatch":"octavian-native" if is_native else "defer-to-runtime-learning",
   "execution_allowed":is_native,"source_urls":sorted(row["source_urls"]),
   "arabic_label":label.get("label") if isinstance(label,dict) else None,
   "learning":None if is_native else {"state":"unresolved","queue":"octavian-runtime-rnn-command-candidates",
    "policy":"RNN ranks evidence and proposes tests only; unknown commands are never executed."}})
 return {"schema":"OCTAVIAN-NATIVE-COMMAND-CANDIDATES-1",
  "policy":"Discovery is not execution. Only the native allowlist is runnable; all other rows require provider, permission, and behavior tests.",
  "native_allowlist":sorted(NATIVE),"common_candidates":sorted(COMMON),
  "counts":{"total":len(commands),"native_implemented":sum(x["status"]=="native-implemented" for x in commands),"candidate_only":sum(x["status"]=="candidate-only" for x in commands)},
  "commands":commands}
def main():
 p=argparse.ArgumentParser();p.add_argument("--source",type=Path,default=DEFAULT_SOURCE);p.add_argument("--ss64",type=Path,default=DEFAULT_SS64);p.add_argument("--arabic",type=Path,default=DEFAULT_ARABIC);p.add_argument("--output",type=Path,default=DEFAULT_OUT);a=p.parse_args()
 data=build(load(a.source),load(a.ss64),load(a.arabic));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print("Imported Octavian native/candidate command inventory:",json.dumps(data["counts"],sort_keys=True))
if __name__=="__main__":main()
