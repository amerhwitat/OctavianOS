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

## 2026-10-22 follow-up — production trace root causes

- The actual production traces show the standard root-directory CPIO entry `. was rejected by the CPIO path validator before Live/Recovery ring-3 entry. PR #120 now permits only the exact `. spelling when the entry is a directory; traversal, absolute paths and non-directory dot entries remain rejected. Regression fixtures now include this conventional root entry.
- The same traces exposed target-menu packaging gaps: Jasper Live/Recovery/Installer menu entries did not consistently pass the separately staged target-matched native init ELF. Native init ELF module lines and fail-closed file guards were added to the top-level and vendored target menus. `tests/migration/test_native_init_module_routing.py` enforces the contract in CI.
- The production CI verifier was also consuming logs from routing smoke tests that intentionally omitted native init modules. The native-kernel workflow now builds target-specific production-payload ISOs and records Live/Installer/Recovery × BIOS/UEFI logs for the unchanged readiness verifier. Routing-only smoke logs remain separate.
- The latest native init still deliberately exits 78 because the real filesystem/process/device/graphics services are not implemented. Therefore these changes fix archive admission and launch plumbing, but do not pass production readiness, Aurora, installer persistence, recovery postcondition, or SMP gates. Exact-head six-case CI must complete and readiness must be proven before release.
