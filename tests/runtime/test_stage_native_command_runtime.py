import tempfile,unittest
from pathlib import Path
from tools.runtime.stage_native_command_runtime import ROOT,TARGETS,stage
class StageRuntimeTests(unittest.TestCase):
 def test_inputs_exist(self):
  self.assertTrue((ROOT/"runtime/commands/native-command-candidates.json").is_file())
  self.assertTrue((ROOT/"runtime/isa/universal-instruction-catalog.json").is_file())
  self.assertEqual(TARGETS[0],ROOT/"vendor/chimera-ii-os/source/rootfs")
  self.assertEqual(TARGETS[1],ROOT/"vendor/chimera-ii-os/source/build/live-boot/initramfs/root")
 def test_stages_both_runtimes(self):
  with tempfile.TemporaryDirectory() as tmp:
   target=Path(tmp)/"root"
   model=Path(tmp)/"trained-model.json"
   model.write_text("test-model",encoding="utf-8")
   stage(target,model)
   for rel in (
    "usr/share/octavian/commands/command_candidate_router.py",
    "usr/share/octavian/commands/local_llm.py",
    "usr/share/octavian/commands/trainable_rnn_lm.py",
    "usr/share/octavian/cognition/trained-command-isa-rnn.json",
    "usr/share/octavian/isa/universal-instruction-catalog.json",
    "usr/share/octavian/isa/isa_candidate_router.py",
    "usr/share/octavian/isa/trainable_rnn_lm.py"):
    self.assertTrue((target/rel).is_file(),rel)
   self.assertTrue((target/"usr/bin/octavian-learn-command").stat().st_mode & 0o111)
   self.assertTrue((target/"usr/bin/octavian-learn-isa").stat().st_mode & 0o111)
   self.assertIn("--rnn-model", (target/"usr/bin/octavian-learn-command").read_text())
   self.assertIn("--rnn-model", (target/"usr/bin/octavian-learn-isa").read_text())
if __name__=="__main__":unittest.main()
