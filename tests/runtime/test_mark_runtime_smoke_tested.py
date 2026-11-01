import importlib.util,json,tempfile,unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[2]/"tools/runtime/mark_runtime_smoke_tested.py"
spec=importlib.util.spec_from_file_location("mark_runtime_smoke_tested",SCRIPT)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class MarkRuntimeSmokeTests(unittest.TestCase):
 def test_marks_host_smoke_without_promoting_os_readiness(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"capabilities.json"
   p.write_text(json.dumps({"schema":"OCTAVIAN-RUNTIME-COGNITION-CAPABILITIES-1","model_trained":True,"in_os_execution_verified":False,"kernel_userspace_ready_verified":False}),encoding="utf-8")
   import sys
   old=sys.argv
   try:
    sys.argv=[str(SCRIPT),str(p)];module.main()
   finally:sys.argv=old
   d=json.loads(p.read_text(encoding="utf-8"))
   self.assertTrue(d["host_router_smoke_tested_in_ci"])
   self.assertFalse(d["in_os_execution_verified"])
   self.assertFalse(d["kernel_userspace_ready_verified"])
if __name__=="__main__":unittest.main()
