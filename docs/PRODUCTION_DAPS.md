# Production DAPS evidence bundle

The release verifier is deliberately fail-closed. It validates an immutable ISO hash,
six target/firmware traces, and separately recorded end-to-end postconditions. A build,
a candidate probe ELF, a manifest, or a kernel-authored readiness line alone cannot pass.

Run:

```sh
python3 tools/release/verify-production-daps.py --evidence build/production-daps/evidence.json
```

All paths in the JSON are relative to the directory containing `evidence.json`.
The candidate ISO must be the exact ISO booted by every trace and end-to-end test.

## Evidence schema (version 1)

```json
{
  "schema_version": 1,
  "iso": "candidate.iso",
  "iso_sha256": "<64 lowercase hex characters>",
  "traces": {
    "live/bios": {"iso_sha256": "<same hash>", "log": "traces/live-bios.log"},
    "live/uefi": {"iso_sha256": "<same hash>", "log": "traces/live-uefi.log"},
    "installer/bios": {"iso_sha256": "<same hash>", "log": "traces/installer-bios.log"},
    "installer/uefi": {"iso_sha256": "<same hash>", "log": "traces/installer-uefi.log"},
    "recovery/bios": {"iso_sha256": "<same hash>", "log": "traces/recovery-bios.log"},
    "recovery/uefi": {"iso_sha256": "<same hash>", "log": "traces/recovery-uefi.log"}
  },
  "installer_persistence": {
    "passed": true, "iso_sha256": "<same hash>", "write_verified": true,
    "cold_reboot_verified": true, "installed_system_ready": true,
    "evidence_log": "traces/installer-persistence.log"
  },
  "recovery": {
    "passed": true, "iso_sha256": "<same hash>", "repair_action_executed": true,
    "postcondition_verified": true, "evidence_log": "traces/recovery-repair.log"
  },
  "smp": {
    "passed": true, "iso_sha256": "<same hash>", "online_ap_cpus": [0, 1],
    "overlap_observed": true, "per_cpu_trace": "traces/smp-overlap.log"
  }
}
```

The values above are a schema example, not real acceptance evidence. Replace every
placeholder with evidence from the same candidate ISO. The verifier also reads the
referenced postcondition logs and requires these exact records:

- Installer log: `INSTALL WRITE VERIFIED`, `INSTALLED DISK COLD REBOOT VERIFIED`,
  `INSTALLED SYSTEM READY`.
- Recovery log: `RECOVERY REPAIR EXECUTED`, `RECOVERY POSTCONDITION VERIFIED`.
- Per-CPU SMP trace: `SMP AP ONLINE: cpu=<id>` for at least two distinct CPUs and
  `SMP OVERLAP VERIFIED`.

Each of the six boot traces must show kernel readiness, a nonzero CPL3-originated
syscall acknowledgement, matching same-PID userspace readiness, and ring-3 return.
Both Live firmware traces must additionally show
`USERSPACE TARGET READY: live component=aurora-session` and `AURORA READY`.

A passing report means these mechanical evidence requirements were met; reviewers must
still inspect provenance, QEMU/firmware configuration, disk snapshots, and per-CPU traces
before approving publication. Never manufacture these records to make the verifier pass.
