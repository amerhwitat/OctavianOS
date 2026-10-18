import json,tempfile,unittest
from pathlib import Path
from tools.commands.import_command_candidates import build
from tools.commands.command_candidate_router import queue_unresolved
class QueueTests(unittest.TestCase):
 def test_unknown_command_is_queued_without_arguments(self):
  catalog=build({"linux":["futurecmd"]},{},{})
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/"pending.jsonl"
   queue_unresolved("futurecmd --token secret",catalog,path)
   text=path.read_text(encoding="utf-8")
   row=json.loads(text.splitlines()[0])
   self.assertEqual(row["command_token"],"futurecmd")
   self.assertNotIn("secret",text)
 def test_exact_native_command_is_not_queued(self):
  catalog=build({"linux":["echo"]},{},{})
  with tempfile.TemporaryDirectory() as tmp:
   self.assertIsNone(queue_unresolved("echo",catalog,Path(tmp)/"pending.jsonl"))
if __name__=="__main__":unittest.main()
