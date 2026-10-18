import unittest
from pathlib import Path
from tools.runtime.stage_native_command_runtime import ROOT,ROOTFS
class StageRuntimeTests(unittest.TestCase):
 def test_inputs_exist(self):
  self.assertTrue((ROOT/"runtime/commands/native-command-candidates.json").is_file())
  self.assertTrue((ROOT/"runtime/isa/universal-instruction-catalog.json").is_file())
  self.assertTrue((ROOTFS/"usr/share").is_dir())
if __name__=="__main__":unittest.main()
