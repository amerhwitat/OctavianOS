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


## Exact-head recheck — 2026-10-22 17:53 UTC

Reviewed branch head: `8289e61af960a684144f8ce19c2bdcb33990634e`.

- [Native Koronos kernel build #39824705866](https://github.com/amerhwitat/OctavianOS/actions/runs/39824705866): pending; no job results available yet.
- [Chimera source integration #39824706139](https://github.com/amerhwitat/OctavianOS/actions/runs/39824706139): queued.
- [Explicit user ELF smoke #39824705572](https://github.com/amerhwitat/OctavianOS/actions/runs/39824705572): queued.
- [Candidate ring-3 smoke #39824705521](https://github.com/amerhwitat/OctavianOS/actions/runs/39824705521): queued; candidate smoke is not production acceptance.
- [Boot target routing #39824705454](https://github.com/amerhwitat/OctavianOS/actions/runs/39824705454), [bounded ingestion #39824705445](https://github.com/amerhwitat/OctavianOS/actions/runs/39824705445), and [artwork/progress #39824705441](https://github.com/amerhwitat/OctavianOS/actions/runs/39824705441): queued.

Re-reading the target launcher confirms the unresolved implementation gap: validated gzip/CPIO bytes are held only in a temporary decompression allocation; the current path does not extract files into a mounted process-visible VFS before entering the separate native init ELF. That init still exits with status 78 because production services are unavailable. These are not grounds to manufacture a readiness marker or weaken the verifier.

No production acceptance is claimed. Keep PR #120 draft and release publication blocked until real rootfs extraction/mounting, target services, Live→Aurora, installer persistence, recovery repair, genuine AP-backed SMP, and all six target/firmware traces pass on the same candidate.


## Exact-head remediation cycle — 2026-10-22 20:35 UTC

- Current OctavianOS PR #120 head: `e946b2336fc905a39618491d7069d5d2128d6ff7`. Latest bounded-ingestion, target-routing, source-integration, artwork, and candidate-smoke workflow runs are queued; explicit ELF smoke is queued for this exact head. Do not infer results before jobs finish.
- The preceding explicit ELF smoke on head `050328b60d33c9f5b32a28cdab6847671de044fc` failed before QEMU boot at `kernel/tests/ramfs_test.cpp:62`. Root cause: RAMFS collapsed all CPIO preflight errors to `CHIMERA_RAMFS_E_HEADER`, obscuring the validator's precise `CHIMERA_CPIO_E_TYPE`. The error-category mapping was corrected in `e946b2336fc905a39618491d7069d5d2128d6ff7`; exact-head rerun is pending.
- The target launcher still does not extract the production archive into a process-visible VFS. A fail-closed guard now prevents production init launch/readiness before rootfs publication. This intentionally makes the missing lifecycle explicit; it does not complete rootfs mounting.
- Release remains BLOCKED. Six full-ISO production cases, Aurora health, installer persistence, recovery postconditions, and AP-backed SMP remain unproven.
