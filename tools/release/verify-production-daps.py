#!/usr/bin/env python3
"""Fail-closed production DAPS verifier for a single immutable Koronos ISO.

Evidence is intentionally external to the verifier: this script never creates
readiness markers, treats build success as runtime success, or promotes probe
ISOs to production. See docs/PRODUCTION_DAPS.md for the evidence schema.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

TARGETS = ("live", "installer", "recovery")
FIRMWARES = ("bios", "uefi")
KERNEL_MARKER = "[KRN ] KORONOS READY"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class GateError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GateError(message)


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"cannot read JSON evidence {path}: {exc}") from exc
    require(isinstance(value, dict), f"{path}: top-level JSON must be an object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise GateError(f"cannot hash {path}: {exc}") from exc
    return digest.hexdigest()


def read_trace(root: Path, item: dict, label: str, expected_sha: str) -> str:
    require(isinstance(item, dict), f"{label}: trace record must be an object")
    iso_sha = item.get("iso_sha256")
    require(iso_sha == expected_sha, f"{label}: trace ISO SHA-256 differs from candidate")
    payload_file = (root / str(item.get("payload_file", ""))).resolve()
    require(payload_file.is_relative_to(root.resolve()), f"{label}: payload path escapes evidence root")
    require(payload_file.is_file(), f"{label}: extracted production init ELF missing: {payload_file}")
    expected_payload_sha = item.get("payload_sha256")
    require(isinstance(expected_payload_sha, str) and SHA256_RE.fullmatch(expected_payload_sha),
            f"{label}: expected production init payload SHA-256 missing from trace evidence")
    actual_payload_sha = sha256_file(payload_file)
    require(actual_payload_sha == expected_payload_sha,
            f"{label}: extracted production init ELF hash mismatch")
    trace_path = (root / str(item.get("log", ""))).resolve()
    require(trace_path.is_relative_to(root.resolve()), f"{label}: trace path escapes evidence root")
    require(trace_path.is_file(), f"{label}: trace file missing: {trace_path}")
    text = trace_path.read_text(encoding="utf-8", errors="replace")
    kernel_at = text.find(KERNEL_MARKER)
    require(kernel_at >= 0, f"{label}: kernel-ready marker missing")

    target = label.split("/")[0]
    ack = list(re.finditer(
        rf"USER INIT SYSCALL: target={re.escape(target)} init_pid=([1-9][0-9]*)",
        text,
    ))
    # Production target readiness is emitted only after the real target
    # component has initialized. Generic USERSPACE READY markers are probe /
    # bootstrap diagnostics and must never satisfy the production gate.
    ready_components = {
        "live": "aurora-session",
        "installer": "install-executor",
        "recovery": "recovery-runtime",
    }
    component = ready_components[target]
    ready = list(re.finditer(
        rf"USERSPACE TARGET READY: {re.escape(target)} component={re.escape(component)} init pid=([1-9][0-9]*)",
        text,
    ))
    require(ack, f"{label}: user-originated CPL3 syscall acknowledgement missing")
    require(ready, f"{label}: userspace readiness marker missing")
    require(kernel_at < ack[-1].start(), f"{label}: syscall acknowledgement precedes kernel readiness")
    require(ack[-1].start() < ready[-1].start(),
            f"{label}: userspace readiness precedes its syscall acknowledgement")
    require(ack[-1].group(1) == ready[-1].group(1),
            f"{label}: syscall acknowledgement PID and ready PID differ")
    ring3_return = text.find("USERSPACE SYSCALL RETURNED TO RING3", ack[-1].start())
    require(ring3_return >= 0, f"{label}: ring-3 return evidence missing")

    # Candidate user-init ELF probes are useful kernel smoke tests, but cannot
    # satisfy production release acceptance. Require explicit provenance from
    # the production initramfs extraction/launch path and bind it to this PID.
    target = label.split("/")[0]
    payload = list(re.finditer(
        rf"PRODUCTION INIT PAYLOAD: target={re.escape(target)} source=initramfs sha256=([0-9a-f]{{64}})",
        text,
    ))
    executed = list(re.finditer(
        rf"PRODUCTION INIT EXECUTED: target={re.escape(target)} pid=([1-9][0-9]*)",
        text,
    ))
    require(payload, f"{label}: production initramfs payload provenance missing (probe ELF is not production evidence)")
    require(executed, f"{label}: production init execution record missing")
    require(executed[-1].start() < ring3_return,
            f"{label}: ring-3 return precedes production init execution")
    require(payload[-1].group(1) == expected_payload_sha,
            f"{label}: production init payload digest differs from independently recorded extracted payload")
    require(payload[-1].start() < ack[-1].start(),
            f"{label}: production payload provenance appears after user execution began")
    require(executed[-1].start() < ready[-1].start(),
            f"{label}: production init execution record appears after readiness")
    require(executed[-1].group(1) == ack[-1].group(1) == ready[-1].group(1),
            f"{label}: production init, syscall acknowledgement, and readiness PIDs differ")
    # Prove the same PID can use the mounted root VFS and writable /tmp from
    # ring 3. A generic syscall acknowledgement alone is not a file-I/O proof.
    pid = ack[-1].group(1)
    open_records = list(re.finditer(
        rf"USERSPACE FILE SYSCALL: target={re.escape(target)} pid={pid} op=open path=/etc/os-release result=fd:([1-9][0-9]*)",
        text,
    ))
    require(open_records, f"{label}: ring-3 rootfs OPEN evidence missing")
    fd = open_records[-1].group(1)
    read_records = list(re.finditer(
        rf"USERSPACE FILE SYSCALL: target={re.escape(target)} pid={pid} op=read path=/etc/os-release fd={fd} result=bytes:([1-9][0-9]*)",
        text,
    ))
    close_records = list(re.finditer(
        rf"USERSPACE FILE SYSCALL: target={re.escape(target)} pid={pid} op=close path=/etc/os-release fd={fd} result=0",
        text,
    ))
    tmp_records = list(re.finditer(
        rf"USERSPACE TMP SYSCALL: target={re.escape(target)} pid={pid} op=write path=/tmp/daps-probe result=bytes:([1-9][0-9]*)",
        text,
    ))
    require(read_records, f"{label}: ring-3 rootfs READ evidence missing")
    require(close_records, f"{label}: ring-3 rootfs CLOSE evidence missing")
    require(tmp_records, f"{label}: ring-3 writable /tmp write evidence missing")
    ready_at = ready[-1].start()
    for name, records in (("OPEN", open_records), ("READ", read_records),
                          ("CLOSE", close_records), ("/tmp WRITE", tmp_records)):
        require(ring3_return < records[-1].start() < ready_at,
                f"{label}: ring-3 {name} evidence is outside the acknowledged init execution window")
    require(open_records[-1].start() < read_records[-1].start() < close_records[-1].start(),
            f"{label}: rootfs OPEN/READ/CLOSE evidence is out of order")

    return text


def read_evidence_log(root: Path, relative: object, label: str, markers: tuple[str, ...]) -> str:
    require(isinstance(relative, str) and bool(relative), f"{label}: evidence log reference missing")
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()), f"{label}: evidence log path escapes evidence root")
    require(path.is_file(), f"{label}: evidence log missing: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    for marker in markers:
        require(marker in text, f"{label}: required evidence record missing: {marker}")
    return text


def safe_evidence_path(root: Path, relative: object, label: str) -> Path:
    require(isinstance(relative, str) and bool(relative), f"{label}: path reference missing")
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()), f"{label}: path escapes evidence root")
    require(path.is_file(), f"{label}: file missing: {path}")
    return path


def read_jsonl_events(path: Path, label: str) -> list[dict]:
    events: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise GateError(f"{label}: cannot read structured event log: {exc}") from exc
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise GateError(f"{label}: line {number} is not a JSON event") from exc
        require(isinstance(event, dict), f"{label}: line {number} must be a JSON object")
        require(isinstance(event.get("event"), str), f"{label}: line {number} lacks event type")
        events.append(event)
    require(events, f"{label}: structured event log is empty")
    return events


def verify_installer_persistence(root: Path, install: object, expected_sha: str) -> None:
    require(isinstance(install, dict), "installer_persistence evidence missing")
    require(install.get("iso_sha256") == expected_sha,
            "installer persistence evidence references a different ISO")
    # Booleans and human-readable markers are not proof of durable media state.
    # Require the actual post-install disk image, byte-for-byte readback, and
    # ordered machine-readable events emitted by the QEMU acceptance harness.
    disk = safe_evidence_path(root, install.get("disk_image"), "installer disk image")
    disk_sha = install.get("disk_image_sha256")
    require(isinstance(disk_sha, str) and SHA256_RE.fullmatch(disk_sha),
            "installer disk image SHA-256 missing")
    require(sha256_file(disk) == disk_sha, "installer disk image SHA-256 mismatch")
    identity = install.get("disk_identity")
    require(isinstance(identity, str) and identity.strip(),
            "installer stable disk identity missing")
    write = install.get("write")
    require(isinstance(write, dict), "installer structured write evidence missing")
    offset = write.get("offset_bytes")
    length = write.get("length_bytes")
    expected_content_sha = write.get("content_sha256")
    require(type(offset) is int and offset >= 0, "installer write offset must be a nonnegative integer")
    require(type(length) is int and length > 0, "installer write length must be a positive integer")
    require(isinstance(expected_content_sha, str) and SHA256_RE.fullmatch(expected_content_sha),
            "installer expected write content SHA-256 missing")
    require(offset + length <= disk.stat().st_size, "installer write range exceeds disk image size")

    readback = safe_evidence_path(root, install.get("readback_file"), "post-reboot disk readback")
    readback_sha = install.get("readback_sha256")
    require(isinstance(readback_sha, str) and SHA256_RE.fullmatch(readback_sha),
            "installer post-reboot readback SHA-256 missing")
    readback_bytes = readback.read_bytes()
    require(len(readback_bytes) == length, "installer readback byte count differs from write length")
    require(hashlib.sha256(readback_bytes).hexdigest() == readback_sha,
            "installer readback artifact SHA-256 mismatch")
    require(readback_sha == expected_content_sha,
            "installer post-reboot readback digest differs from expected written content")
    with disk.open("rb") as stream:
        stream.seek(offset)
        disk_bytes = stream.read(length)
    require(len(disk_bytes) == length, "installer disk image readback is truncated")
    require(hashlib.sha256(disk_bytes).hexdigest() == expected_content_sha,
            "installer disk image does not contain expected persisted bytes at write range")
    require(disk_bytes == readback_bytes,
            "installer post-reboot readback bytes differ from the installed disk image")
    require(sha256_file(disk) == disk_sha,
            "installer disk image changed while persistence evidence was being verified")

    event_path = safe_evidence_path(root, install.get("evidence_log"), "installer structured evidence log")
    events = read_jsonl_events(event_path, "installer persistence")
    kinds = [event["event"] for event in events]
    required = ("install_write", "vm_stopped", "vm_started", "disk_readback", "installed_system_ready")
    positions = {}
    for kind in required:
        found = [i for i, event in enumerate(events) if event.get("event") == kind]
        require(len(found) == 1, f"installer evidence must contain exactly one {kind} event")
        positions[kind] = found[0]
    require([positions[k] for k in required] == sorted(positions.values()),
            "installer write/stop/cold-start/readback/installed-ready events are out of order")
    write_event = events[positions["install_write"]]
    require(write_event.get("disk_identity") == identity
            and write_event.get("offset_bytes") == offset
            and write_event.get("length_bytes") == length
            and write_event.get("content_sha256") == expected_content_sha
            and write_event.get("flush_sync") is True,
            "installer write event does not prove the expected range, digest, and successful flush/sync")
    stopped = events[positions["vm_stopped"]]
    started = events[positions["vm_started"]]
    require(stopped.get("cold_stop") is True and isinstance(stopped.get("vm_id"), str)
            and stopped.get("vm_id"), "installer first VM stop is not confirmed as a cold stop")
    require(isinstance(started.get("vm_id"), str) and started.get("vm_id")
            and started.get("vm_id") != stopped.get("vm_id"),
            "installer cold reboot must use a distinct VM instance")
    require(isinstance(stopped.get("session_id"), str) and stopped.get("session_id")
            and isinstance(started.get("session_id"), str) and started.get("session_id")
            and started.get("session_id") != stopped.get("session_id"),
            "installer cold reboot must use a distinct QEMU session")
    require(started.get("cold_start") is True
            and started.get("disk_identity") == identity
            and started.get("disk_image_sha256") == disk_sha,
            "installer second VM did not cold-start the same verified disk image")
    read_event = events[positions["disk_readback"]]
    require(read_event.get("disk_identity") == identity
            and read_event.get("offset_bytes") == offset
            and read_event.get("length_bytes") == length
            and read_event.get("content_sha256") == expected_content_sha
            and read_event.get("after_cold_start") is True,
            "installer readback event is not tied to the same disk/range after cold start")
    ready = events[positions["installed_system_ready"]]
    require(ready.get("vm_id") == started.get("vm_id")
            and ready.get("disk_identity") == identity
            and ready.get("disk_image_sha256") == disk_sha,
            "installed-system readiness is not bound to the second VM and same disk artifact")

def verify(evidence_path: Path, report: bool = True) -> None:
    root = evidence_path.resolve().parent
    evidence = read_json(evidence_path)
    require(evidence.get("schema_version") == 2, "schema_version must be 2 for artifact-backed installer persistence")
    iso_path = (root / str(evidence.get("iso", ""))).resolve()
    require(iso_path.is_relative_to(root), "ISO path escapes evidence root")
    require(iso_path.is_file(), "candidate ISO is missing")
    expected_sha = str(evidence.get("iso_sha256", ""))
    require(bool(SHA256_RE.fullmatch(expected_sha)), "iso_sha256 must be lowercase SHA-256")
    actual_sha = sha256_file(iso_path)
    require(actual_sha == expected_sha, f"candidate ISO hash mismatch: expected {expected_sha}, got {actual_sha}")
    with iso_path.open("rb") as stream:
        stream.seek(16 * 2048)
        primary_volume_descriptor = stream.read(7)
    require(primary_volume_descriptor == b"\x01CD001\x01",
            "candidate does not contain an ISO9660 primary volume descriptor at sector 16")

    traces = evidence.get("traces")
    require(isinstance(traces, dict), "traces must be an object")
    trace_text: dict[str, str] = {}
    for target in TARGETS:
        for firmware in FIRMWARES:
            label = f"{target}/{firmware}"
            require(label in traces, f"missing required production trace {label}")
            trace_text[label] = read_trace(root, traces[label], label, expected_sha)

    for firmware in FIRMWARES:
        live = trace_text[f"live/{firmware}"]
        require("USERSPACE TARGET READY: live component=aurora-session" in live,
                f"Live/{firmware}: actual Aurora session readiness missing")
        require("AURORA READY" in live, f"Live/{firmware}: Aurora runtime health marker missing")

    verify_installer_persistence(root, evidence.get("installer_persistence"), expected_sha)

    recovery = evidence.get("recovery")
    require(isinstance(recovery, dict), "recovery evidence missing")
    require(recovery.get("passed") is True, "recovery repair not accepted")
    require(recovery.get("iso_sha256") == expected_sha, "recovery evidence references a different ISO")
    require(recovery.get("repair_action_executed") is True, "recovery repair action not executed")
    require(recovery.get("postcondition_verified") is True, "recovery repair postcondition not verified")
    read_evidence_log(root, recovery.get("evidence_log"), "recovery repair", (
        "RECOVERY REPAIR EXECUTED",
        "RECOVERY POSTCONDITION VERIFIED",
    ))

    smp = evidence.get("smp")
    require(isinstance(smp, dict), "SMP evidence missing")
    require(smp.get("passed") is True, "AP-backed concurrent SMP not accepted")
    require(smp.get("iso_sha256") == expected_sha, "SMP evidence references a different ISO")
    require(isinstance(smp.get("online_ap_cpus"), list) and len(set(smp["online_ap_cpus"])) >= 2,
            "SMP requires at least two distinct online CPU IDs including AP evidence")
    require(smp.get("overlap_observed") is True, "overlapping execution evidence missing")
    smp_log = read_evidence_log(root, smp.get("per_cpu_trace"), "SMP", ("SMP OVERLAP VERIFIED",))
    observed_cpus = set(re.findall(r"SMP AP ONLINE: cpu=([0-9]+)", smp_log))
    declared_cpus = {str(cpu) for cpu in smp["online_ap_cpus"]}
    require(len(observed_cpus) >= 2, "SMP trace must show at least two AP-online CPU records")
    require(declared_cpus.issubset(observed_cpus), "SMP declared CPU IDs are not all present in per-CPU trace")

    if report:
        print("PRODUCTION DAPS: PASS")
        print(f"ISO SHA-256: {expected_sha}")
        print("Runtime matrix: Live/Installer/Recovery × BIOS/UEFI: 6/6")
        print("Aurora, installer cold-reboot persistence, recovery postconditions, and AP-backed SMP: PASS")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path,
                        help="JSON evidence manifest; paths are relative to its directory")
    args = parser.parse_args()
    try:
        verify(args.evidence)
    except GateError as exc:
        print(f"PRODUCTION DAPS: BLOCKED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
