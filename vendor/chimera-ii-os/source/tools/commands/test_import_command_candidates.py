import unittest
from tools.commands.import_command_candidates import build,NATIVE
class CandidateTests(unittest.TestCase):
 def test_only_allowlist_is_executable(self):
  d=build({"linux_bash":["echo","future-command"]},{},{})
  rows={x["normalized_name"]:x for x in d["commands"]}
  self.assertTrue(rows["echo"]["execution_allowed"])
  self.assertFalse(rows["future-command"]["execution_allowed"])
 def test_unknown_command_stays_queued(self):
  d=build({"x":["future-command"]},{},{})
  row=next(x for x in d["commands"] if x["name"]=="future-command")
  self.assertEqual(row["learning"]["state"],"unresolved")
  self.assertTrue(NATIVE.issubset(set(d["native_allowlist"])))
if __name__=="__main__":unittest.main()
