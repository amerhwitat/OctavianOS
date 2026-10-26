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
        # Synthetic ISO9660 PVD fixture; this is not a bootable OS image.
        iso = bytearray(16 * 2048 + 7)
        iso[16 * 2048:16 * 2048 + 7] = b"\x01CD001\x01"
        (self.root / "candidate.iso").write_bytes(iso)
        self.sha = hashlib.sha256((self.root / "candidate.iso").read_bytes()).hexdigest()
        traces = {}
        payload_hashes = {}
        for target in ("live", "installer", "recovery"):
            payload = self.root / f"{target}-production-init.elf"
            payload.write_bytes(f"test production init payload for {target}".encode())
            payload_hashes[target] = hashlib.sha256(payload.read_bytes()).hexdigest()
            for firmware in ("bios", "uefi"):
                lines = [
                    "[KRN ] KORONOS READY",
                    f"PRODUCTION INIT PAYLOAD: target={target} source=initramfs sha256={payload_hashes[target]}",
                    f"PRODUCTION INIT EXECUTED: target={target} pid=42",
                    f"USER INIT SYSCALL: target={target} init_pid=42",
                    "USERSPACE SYSCALL RETURNED TO RING3",
                    f"USERSPACE FILE SYSCALL: target={target} pid=42 op=open path=/etc/os-release result=fd:3",
                    f"USERSPACE FILE SYSCALL: target={target} pid=42 op=read path=/etc/os-release fd=3 result=bytes:16",
                    f"USERSPACE FILE SYSCALL: target={target} pid=42 op=close path=/etc/os-release fd=3 result=0",
                    f"USERSPACE TMP SYSCALL: target={target} pid=42 op=write path=/tmp/daps-probe result=bytes:4",
                    f"USERSPACE READY: {target} init pid=42",
                ]
                if target == "live":
                    lines += ["USERSPACE TARGET READY: live component=aurora-session", "AURORA READY"]
                name = f"{target}-{firmware}.log"
                (self.root / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
                traces[f"{target}/{firmware}"] = {
                    "iso_sha256": self.sha, "log": name,
                    "payload_file": payload.name, "payload_sha256": payload_hashes[target],
                }

        # A real byte-range fixture exercises disk identity, sync, distinct VM
        # sessions, cold-start ordering, and byte-for-byte post-reboot readback.
        disk_bytes = bytearray(4096)
        persisted = b"installed-system-persistence-proof"
        offset = 512
        disk_bytes[offset:offset + len(persisted)] = persisted
        disk = self.root / "installed-disk.img"
        disk.write_bytes(disk_bytes)
        disk_sha = hashlib.sha256(disk.read_bytes()).hexdigest()
        content_sha = hashlib.sha256(persisted).hexdigest()
        (self.root / "post-reboot-readback.bin").write_bytes(persisted)
        events = [
            {"event":"install_write","disk_identity":"qemu-disk:serial-001","offset_bytes":offset,
             "length_bytes":len(persisted),"content_sha256":content_sha,"flush_sync":True},
            {"event":"vm_stopped","vm_id":"vm-first","session_id":"session-first","cold_stop":True},
            {"event":"vm_started","vm_id":"vm-second","session_id":"session-second","cold_start":True,
             "disk_identity":"qemu-disk:serial-001","disk_image_sha256":disk_sha},
            {"event":"disk_readback","disk_identity":"qemu-disk:serial-001","offset_bytes":offset,
             "length_bytes":len(persisted),"content_sha256":content_sha,"after_cold_start":True},
            {"event":"installed_system_ready","vm_id":"vm-second","disk_identity":"qemu-disk:serial-001",
             "disk_image_sha256":disk_sha},
        ]
        (self.root / "installer-events.jsonl").write_text(
            "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
        (self.root / "recovery-repair.log").write_text(
            "RECOVERY REPAIR EXECUTED\nRECOVERY POSTCONDITION VERIFIED\n", encoding="utf-8")
        (self.root / "smp.log").write_text(
            "SMP AP ONLINE: cpu=0\nSMP AP ONLINE: cpu=1\nSMP OVERLAP VERIFIED\n", encoding="utf-8")
        self.evidence = {
            "schema_version": 2, "iso": "candidate.iso", "iso_sha256": self.sha, "traces": traces,
            "installer_persistence": {
                "iso_sha256": self.sha, "disk_image": "installed-disk.img", "disk_image_sha256": disk_sha,
                "disk_identity": "qemu-disk:serial-001",
                "write": {"offset_bytes": offset, "length_bytes": len(persisted), "content_sha256": content_sha},
                "readback_file": "post-reboot-readback.bin", "readback_sha256": content_sha,
                "evidence_log": "installer-events.jsonl",
            },
            "recovery": {"passed": True, "iso_sha256": self.sha, "repair_action_executed": True,
                         "postcondition_verified": True, "evidence_log": "recovery-repair.log"},
            "smp": {"passed": True, "iso_sha256": self.sha, "online_ap_cpus": [0, 1],
                    "overlap_observed": True, "per_cpu_trace": "smp.log"},
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
        (self.root / "live-bios.log").write_text(
            "[KRN ] KORONOS READY\nUSER INIT SYSCALL: target=live init_pid=42\n"
            "USERSPACE READY: live init pid=42\nUSERSPACE SYSCALL RETURNED TO RING3\n",
            encoding="utf-8")
        with self.assertRaisesRegex(DAPS.GateError, "production initramfs payload provenance missing"):
            DAPS.verify(self.manifest)

    def test_rejects_missing_ring3_rootfs_or_tmp_io_evidence(self):
        path = self.root / "live-bios.log"
        lines = [line for line in path.read_text(encoding="utf-8").splitlines()
                 if "op=write path=/tmp/daps-probe" not in line]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(DAPS.GateError, "ring-3 writable /tmp write evidence missing"):
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
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(DAPS.GateError, "readiness precedes its syscall acknowledgement"):
            DAPS.verify(self.manifest)

    def test_rejects_trace_from_different_iso(self):
        self.evidence["traces"]["recovery/uefi"]["iso_sha256"] = "0" * 64
        self.write_manifest()
        with self.assertRaisesRegex(DAPS.GateError, "differs from candidate"):
            DAPS.verify(self.manifest)

    def test_rejects_disk_image_changed_after_manifest_hash(self):
        with (self.root / "installed-disk.img").open("ab") as stream:
            stream.write(b"tamper")
        with self.assertRaisesRegex(DAPS.GateError, "installer disk image SHA-256 mismatch"):
            DAPS.verify(self.manifest)

    def test_rejects_forged_cold_reboot_using_same_vm(self):
        event_path = self.root / "installer-events.jsonl"
        events = [json.loads(line) for line in event_path.read_text().splitlines()]
        events[2]["vm_id"] = "vm-first"
        event_path.write_text("".join(json.dumps(e) + "\n" for e in events))
        with self.assertRaisesRegex(DAPS.GateError, "distinct VM instance"):
            DAPS.verify(self.manifest)

    def test_rejects_missing_ap_overlap_record(self):
        (self.root / "smp.log").write_text("SMP AP ONLINE: cpu=0\nSMP AP ONLINE: cpu=1\n", encoding="utf-8")
        with self.assertRaisesRegex(DAPS.GateError, "SMP OVERLAP VERIFIED"):
            DAPS.verify(self.manifest)

    def test_rejects_missing_aurora_in_one_firmware(self):
        path = self.root / "live-uefi.log"
        lines = [line for line in path.read_text(encoding="utf-8").splitlines()
                 if line not in {"USERSPACE TARGET READY: live component=aurora-session", "AURORA READY"}]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(DAPS.GateError, "Live/uefi: actual Aurora"):
            DAPS.verify(self.manifest)


if __name__ == "__main__":
    unittest.main()
