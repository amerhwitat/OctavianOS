import importlib.util,json,tempfile,unittest
from pathlib import Path
SCRIPT=Path(__file__).resolve().parents[2]/"tools/runtime/train_runtime_rnn.py"
spec=importlib.util.spec_from_file_location("octavian_train_runtime_rnn",SCRIPT)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class RuntimeRNNTrainingTests(unittest.TestCase):
 def test_corpus_uses_command_and_isa_rows_and_keeps_status_labels(self):
  with tempfile.TemporaryDirectory() as tmp:
   commands=Path(tmp)/"commands.json";isa=Path(tmp)/"isa.json"
   commands.write_text(json.dumps({"counts":{"total":1},"commands":[{"name":"echo","status":"native-implemented","provider":"chimera-cmd","target":"linux"}]}))
   isa.write_text(json.dumps({"instructions":[{"architecture":"riscv32","mnemonic":"ADD","form_id":"rv32i.add","encoding_status":"sourced-mask-verified","execution_status":"not-implemented"}]}))
   rows,cmd,ins=module.corpus_from(commands,isa)
   self.assertTrue(any("command echo" in row and "native-implemented" in row for row in rows))
   self.assertTrue(any("instruction riscv32 ADD" in row and "not-implemented" in row for row in rows))
   self.assertEqual(cmd["counts"]["total"],1);self.assertEqual(len(ins["instructions"]),1)
if __name__=="__main__":unittest.main()
