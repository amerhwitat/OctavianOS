#!/usr/bin/env python3
"""Contract test for binding exact-ISO QEMU traces into a fail-closed report."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/collect-production-closeout-evidence.py"
SPEC = importlib.util.spec_from_file_location("closeout_collector", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class ProductionTraceBindingContract(unittest.TestCase):
    def test_six_same_iso_traces_are_bound_but_blocked_gates_stay_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "out"
            output.mkdir()
            iso = output / "chimera-ii-os.iso"
            iso.write_bytes(b"exact ISO fixture")
            digest = hashlib.sha256(iso.read_bytes()).hexdigest()
            matrix = output / "production-qemu-matrix"
            traces = root / "candidate-traces"
            traces.mkdir()
            cases = []
            for target in ("live", "installer", "recovery"):
                for firmware in ("bios", "uefi"):
                    case_id = f"{target}-{firmware}"
                    case_dir = matrix / case_id
                    case_dir.mkdir(parents=True)
                    trace = f"PRODUCTION ISO SHA-256: {digest}\\n[KRN ] KORONOS READY\\n"
                    (case_dir / "raw-trace.log").write_text(trace, encoding="utf-8")
                    cases.append({"case": case_id, "status": "BLOCKED", "qemu_started": True, "trace": f"{case_id}/raw-trace.log"})
            (matrix / "matrix-report.json").write_text(json.dumps({
                "schema": "CHM-PRODUCTION-ISO-QEMU-MATRIX-1",
                "iso_sha256": digest, "iso_sha256_after": digest, "cases": cases,
            }), encoding="utf-8")
            data = MODULE.collect(iso, output, traces, matrix)
            report = json.loads((output / "production-closeout-evidence.json").read_text())
        self.assertFalse(report["candidate_smoke_substituted"])
        self.assertEqual(report["production_iso_sha256"], digest)
        self.assertTrue(all(c["candidate_trace_is_production_evidence"] for c in report["cases"].values()))
        self.assertTrue(all(c["status"] == "BLOCKED" for c in report["cases"].values()))
        self.assertTrue(all(c["raw_trace"].endswith("-production-iso.log") for c in report["cases"].values()))
        self.assertEqual(report["smp"]["status"], "NOT RUN")
        self.assertEqual(report["installer_persistence"]["status"], "NOT RUN")


if __name__ == "__main__":
    unittest.main(verbosity=2)
