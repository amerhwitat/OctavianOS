import unittest
from runtime.commands.import_candidates import ROOT
class RuntimeBridgeTests(unittest.TestCase):
 def test_vendored_runtime_exists(self): self.assertTrue((ROOT/"vendor/chimera-ii-os/source/tools/commands/import_command_candidates.py").is_file())
if __name__=="__main__":unittest.main()
