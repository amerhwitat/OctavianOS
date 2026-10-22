# OctavianOS Production Acceptance Ledger — 2026-10-22

This ledger distinguishes source changes and candidate smoke tests from production destination acceptance.

## Current evidence

- The bounded gzip/DEFLATE and strict newc CPIO work is under review in [PR #120](https://github.com/amerhwitat/OctavianOS/pull/120). Exact-head CI was queued at the last poll.
- The production target ELF launch integration is under review in [PR #93](https://github.com/amerhwitat/OctavianOS/pull/93). Its workflows were also queued at the last poll.
- A previous completed shared-runtime full-ISO run failed its actual userspace-handoff gate under both BIOS and UEFI after ISO composition and early kernel-ready smoke. Native init deliberately exits 78 when target services are unavailable. Do not infer a pass from an isolated ring-3 probe.
- This prior run is not the exact head of PR #120. Its result is historical evidence; the current PR head must be evaluated independently when its workflows finish.

## Production case matrix

| Case | Historical result | Acceptance required |
|---|---|---|
| Live / BIOS | FAIL | Real Live process, user-originated syscall acknowledgement, matching nonzero PID, Aurora session health |
| Installer / BIOS | FAIL | Real installer process, disposable-disk transaction, cold reboot and read-back |
| Recovery / BIOS | FAIL | Real recovery process and verified repair postcondition |
| Live / UEFI | FAIL | Real Live process, user-originated syscall acknowledgement, matching nonzero PID, Aurora session health |
| Installer / UEFI | FAIL | Real installer process, disposable-disk transaction, cold reboot and read-back |
| Recovery / UEFI | FAIL | Real recovery process and verified repair postcondition |
| AP-backed SMP | NOT IMPLEMENTED / NOT RUN | AP startup and overlapping execution on distinct CPUs with per-CPU evidence |

## Required dependency order

1. Bounded decompression and strict CPIO validation.
2. Safe extraction into a process-visible VFS/root namespace; reject traversal, duplicate/conflicting paths, unsupported types and resource exhaustion.
3. Process-owned descriptors, user-memory validation, and implemented read/write/map/unmap/exit/wait/reap semantics.
4. A real target-specific init process and supervisor; no kernel-authored or probe-only readiness markers.
5. Target services and health checks: Live session, installer executor, and recovery runtime.
6. Installer durable write → cold reboot → read-back; recovery repair → verify postcondition.
7. AP startup and actual concurrent per-CPU scheduler execution.
8. Run all six production target/firmware cases on the final ISO, preserve exact ISO/payload hashes and raw logs, and record PASS/FAIL/NOT RUN.

The release gate must remain fail-closed. Do not publish a production release until every required case passes on the exact release candidate.