"""Unit tests for the fail-closed production DAPS verifier."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/release/verify-production-daps.py"
SPEC = importlib.util.spec_from_file_location("production_daps", SCRIPT)
DAPS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DAPS)


class ProductionDAPSTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        # Minimal synthetic ISO9660 PVD signature fixture; not a bootable OS image.
        iso_bytes = bytearray(16 * 2048 + 7)
        iso_bytes[16 * 2048:16 * 2048 + 7] = b"\x01CD001\x01"
        (self.root / "candidate.iso").write_bytes(iso_bytes)
        self.sha = hashlib.sha256((self.root / "candidate.iso").read_bytes()).hexdigest()
        traces = {}
        payload_hashes = {}
        for target in ("live", "installer", "recovery"):
            payload_path = self.root / f"{target}-production-init.elf"
            payload_path.write_bytes(f"test production init payload for {target}".encode("utf-8"))
            payload_hashes[target] = hashlib.sha256(payload_path.read_bytes()).hexdigest()
            for firmware in ("bios", "uefi"):
                label = f"{target}/{firmware}"
                lines = [
                    "[KRN ] KORONOS READY",
                    f"PRODUCTION INIT PAYLOAD: target={target} source=initramfs sha256={payload_hashes[target]}",
                    f"PRODUCTION INIT EXECUTED: target={target} pid=42",
                    f"USER INIT SYSCALL: target={target} init_pid=42",
                    "USERSPACE SYSCALL RETURNED TO RING3",
                    f"USERSPACE READY: {target} init pid=42",
                ]
                if target == "live":
                    lines += [
                        "USERSPACE TARGET READY: live component=aurora-session",
                        "AURORA READY",
                    ]
                filename = f"{target}-{firmware}.log"
                (self.root / filename).write_text("\n".join(lines) + "\n", encoding="utf-8")
                traces[label] = {
                    "iso_sha256": self.sha, "log": filename,
                    "payload_file": f"{target}-production-init.elf",
                    "payload_sha256": payload_hashes[target],
                }
        (self.root / "installer-persistence.log").write_text(
            "INSTALL WRITE VERIFIED\nINSTALLED DISK COLD REBOOT VERIFIED\nINSTALLED SYSTEM READY\n",
            encoding="utf-8")
        (self.root / "recovery-repair.log").write_text(
            "RECOVERY REPAIR EXECUTED\nRECOVERY POSTCONDITION VERIFIED\n", encoding="utf-8")
        (self.root / "smp.log").write_text(
            "SMP AP ONLINE: cpu=0\nSMP AP ONLINE: cpu=1\nSMP OVERLAP VERIFIED\n", encoding="utf-8")
        self.evidence = {
            "schema_version": 1, "iso": "candidate.iso", "iso_sha256": self.sha, "traces": traces,
            "installer_persistence": {
                "passed": True, "iso_sha256": self.sha, "write_verified": True,
                "cold_reboot_verified": True, "installed_system_ready": True,
                "evidence_log": "installer-persistence.log",
            },
            "recovery": {
                "passed": True, "iso_sha256": self.sha, "repair_action_executed": True,
                "postcondition_verified": True, "evidence_log": "recovery-repair.log",
            },
            "smp": {
                "passed": True, "iso_sha256": self.sha, "online_ap_cpus": [0, 1],
                "overlap_observed": True, "per_cpu_trace": "smp.log",
            },
        }
        self.manifest = self.root / "evidence.json"
        self.write_manifest()

    def tearDown(self):
        self.tmp.cleanup()

    def write_manifest(self):
        self.manifest.write_text(json.dumps(self.evidence), encoding="utf-8")

    def test_complete_fixture_satisfies_mechanical_contract(self):
        DAPS.verify(self.manifest, report=False)

    def test_rejects_probe_only_trace_without_production_payload_provenance(self):
        path = self.root / "live-bios.log"
        path.write_text(
            "[KRN ] KORONOS READY\\n"
            "USER INIT SYSCALL: target=live init_pid=42\\n"
            "USERSPACE READY: live init pid=42\\n"
            "USERSPACE SYSCALL RETURNED TO RING3\\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(DAPS.GateError, "production initramfs payload provenance missing"):
            DAPS.verify(self.manifest)

    def test_rejects_extracted_init_payload_hash_mismatch(self):
        self.evidence["traces"]["live/bios"]["payload_sha256"] = "0" * 64
        self.write_manifest()
        with self.assertRaisesRegex(DAPS.GateError, "extracted production init ELF hash mismatch"):
            DAPS.verify(self.manifest)

    def test_rejects_readiness_before_cpl3_acknowledgement(self):
        path = self.root / "live-bios.log"
        lines = path.read_text(encoding="utf-8").splitlines()
        ack = next(i for i, line in enumerate(lines) if line.startswith("USER INIT SYSCALL:"))
        ready = next(i for i, line in enumerate(lines) if line.startswith("USERSPACE READY:"))
        lines[ack], lines[ready] = lines[ready], lines[ack]
        path.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
        with self.assertRaisesRegex(DAPS.GateError, "readiness precedes its syscall acknowledgement"):
            DAPS.verify(self.manifest)

    def test_rejects_trace_from_different_iso(self):
        self.evidence["traces"]["recovery/uefi"]["iso_sha256"] = "0" * 64
        self.write_manifest()
        with self.assertRaisesRegex(DAPS.GateError, "differs from candidate"):
            DAPS.verify(self.manifest)

    def test_rejects_missing_ap_overlap_record(self):
        (self.root / "smp.log").write_text("SMP AP ONLINE: cpu=0\nSMP AP ONLINE: cpu=1\n", encoding="utf-8")
        with self.assertRaisesRegex(DAPS.GateError, "SMP OVERLAP VERIFIED"):
            DAPS.verify(self.manifest)

    def test_rejects_missing_aurora_in_one_firmware(self):
        (self.root / "live-uefi.log").write_text(
            "[KRN ] KORONOS READY\\nUSER INIT SYSCALL: target=live init_pid=42\\n"
            "USERSPACE READY: live init pid=42\\nUSERSPACE SYSCALL RETURNED TO RING3\\n"
            "PRODUCTION INIT PAYLOAD: target=live source=initramfs sha256=" + "a" * 64 + "\\n"
            "PRODUCTION INIT EXECUTED: target=live pid=42\\n",
            encoding="utf-8")
        with self.assertRaisesRegex(DAPS.GateError, "Live/uefi: actual Aurora"):
            DAPS.verify(self.manifest)


if __name__ == "__main__":
    unittest.main()
