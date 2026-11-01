#!/usr/bin/env python3
"""Record host-side router smoke evidence without upgrading in-OS readiness."""
import json,os,sys
from pathlib import Path
def main():
 if len(sys.argv)!=2:raise SystemExit("usage: mark_runtime_smoke_tested.py CAPABILITIES_JSON")
 p=Path(sys.argv[1]);d=json.loads(p.read_text(encoding="utf-8"))
 if d.get("schema")!="OCTAVIAN-RUNTIME-COGNITION-CAPABILITIES-1" or not d.get("model_trained"):
  raise SystemExit("refusing to mark an unknown or untrained model report")
 d["host_router_smoke_tested_in_ci"]=True
 d["host_smoke_commit"]=os.environ.get("GITHUB_SHA","local")
 d["host_smoke_run_id"]=os.environ.get("GITHUB_RUN_ID","local")
 d["status"]="staged-host-smoke-tested"
 d["in_os_execution_verified"]=False
 d["kernel_userspace_ready_verified"]=False
 p.write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
 print("Marked host router smoke-tested; kept in-OS execution and userspace readiness unverified.")
if __name__=="__main__":main()
