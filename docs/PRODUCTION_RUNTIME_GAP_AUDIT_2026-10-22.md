# Production Runtime Gap Audit — 2026-10-22

## Scope and evidence boundary

Reviewed the native syscall dispatcher, target launch path, ELF loader, scheduler and service bootstrap, native init, acceptance workflow, recent workflow listings, and the production handoff notes in the project Library. This is a focused source audit, not a claim that every repository file has been exhaustively built or executed.

## Confirmed implementation gaps

1. **The staged native init remains an ABI smoke probe.** `vendor/chimera-ii-os/source/kernel/userspace/native_init.c` performs a CPL3 acknowledgement, GETPID, target-payload envelope/metadata validation, prints `USERSPACE READY: <target> init pid=<N>`, and exits. It does not extract the initramfs, mount a filesystem, exec the archive's `/init`, supervise services, start Aurora, execute an installation, or provide a recovery shell.
2. **The target-launch path validates but does not execute payloads.** `vendor/chimera-ii-os/source/kernel/core/target_launch.cpp` accepts a gzip magic prefix or a raw newc CPIO magic prefix for Live/Recovery; it does not decompress/extract the archive or verify that a runnable target init and its dependencies are present. Installer metadata checks are only envelope/leading-character checks, not a full schema validation or install transaction.
3. **Syscall coverage is incomplete.** `vendor/chimera-ii-os/source/kernel/core/syscall.cpp` supports a limited native path (GETPID, YIELD, TICKS, payload validation, console WRITE, and EXIT sentinel). Declared READ, MMAP, MUNMAP, IOCTL, NANOSLEEP, WAIT, and ARCH_PRCTL are not a complete usable process/filesystem ABI. Compatibility dispatch rejects operations that lack a real process context; keep that behavior fail-closed.
4. **Scheduler is not SMP.** `vendor/chimera-ii-os/source/kernel/core/scheduler.cpp` explicitly returns zero from `chimera_sched_run_parallel()` because AP workers do not enter the scheduler on independent CPUs. Sequential callbacks cannot satisfy the SMP gate.
5. **Service bootstrap is declaration-only.** `vendor/chimera-ii-os/source/kernel/core/service.cpp` declares core services and resolves dependency order, but the bootstrap comments state that it does not start services. Storage is not ready until a backend, mount, start callback and health check succeed.
6. **Readiness is not production behavior.** The native init does not emit the required target-owned service marker. The target launch gate now requires the relevant service marker and rejects a generic probe's clean exit, but the actual service implementations and independent health checks remain absent.
7. **Production destinations remain unproven.** No completed evidence currently establishes usable Aurora, an installation that survives reboot, an operational recovery shell, durable storage, or all six production target/firmware boots.

## Required engineering sequence

1. Implement bounded newc CPIO parsing and safe extraction, plus gzip/DEFLATE support or a fail-closed unsupported-compression error; reject path traversal, absolute paths, malformed headers, integer overflow, and missing trailers.
2. Implement VFS/RAMFS mounting, safe user-copy, descriptors and functional READ/WRITE/MAP/UNMAP operations bound to process-owned address spaces.
3. Implement process lifecycle and PID-1 supervision: create/exec, wait/reap, exit teardown, fault handling, and bounded target-specific service startup.
4. Add actual Live/Aurora, Installer, and Recovery service executables. Readiness must be backed by service-owned initialization and an independent health check—not a string emitted by the generic native init.
5. Verify a real installer transaction against disposable storage, reboot into the installed system, and read back persisted state after cold reboot.
6. Bring up APs and run scheduler workers concurrently, with per-CPU traces proving overlap rather than simulated sequencing.
7. Execute all six production ISO cases (Live/Installer/Recovery × BIOS/UEFI). Preserve ISO/payload SHA-256, command lines, raw boot traces, service health results, exit codes, and explicit PASS/FAIL/NOT RUN.

## Release policy

Keep acceptance fail-closed. Generic init markers, candidate probe ISOs, static routing contracts, or green desktop/catalog workflows do not establish production userspace readiness. Do not merge the draft or publish a production ISO until destination and SMP evidence is complete.

## External architecture references

- Linux kernel initramfs/rootfs format and extraction lifecycle: https://www.kernel.org/doc/html/v6.5/filesystems/ramfs-rootfs-initramfs.html
- Limine boot protocol contract: https://github.com/limine-bootloader/limine-protocol/blob/trunk/PROTOCOL.md

These references inform the design; no third-party implementation was copied into the kernel without license review, integration and tests.


## Follow-up evidence — 2026-10-22

Production acceptance run 39774382031 has a completed FAILURE for recovery/UEFI (job 119809533041); the other five matrix jobs were still queued at the last poll, so they are NOT RUN/pending, not passes. The failed job built Koronos and high-address userspace probes, classified the recovery module, built a target-specific ISO, and attempted the userspace readiness gate. The log shows generic USERSPACE READY: recovery init pid=1, then a userspace exit; the launcher reports init exited before its target-specific handshake and explicitly states recovery handoff is withheld because no native recovery init ELF/runtime is wired to the payload. Runnable task count is zero.

The log also prints PASS: ordered kernel/user-syscall/userspace-ready trace target=recovery pid=1. This is a narrow trace-order/probe assertion, not proof of a usable recovery service; the job's final conclusion is failure. Do not let this sub-check mask the service readiness gate.

## Implementation/acceptance ledger

- [ ] Bounded newc CPIO parser with overflow-safe bounds, header/name/data validation, alignment and trailer checks.
- [ ] Bounded gzip/DEFLATE decompression with strict expanded-size limits; reject unknown compression instead of treating it as CPIO.
- [ ] Safe extraction with path traversal/absolute-path rejection, entry and byte caps, duplicate/type-conflict handling, and symlink escape prevention.
- [ ] Mount extracted rootfs in VFS; connect process-owned file descriptors and checked user-buffer copies to real file operations; keep unsupported syscalls fail-closed.
- [ ] Implement real process exec/exit/wait/reap and deterministic address-space/FD cleanup.
- [ ] Start and health-check target services: Live/Aurora session, Installer transaction executor, Recovery shell/runtime. Emit each target marker only after the corresponding service passes its health check.
- [ ] Verify installer writes to disposable storage and survives cold reboot; verify genuine AP startup and concurrent execution on separate CPUs.
- [ ] Complete six independent target/firmware cases with artifact hashes, boot logs, same-process syscall/PID evidence, service health logs, and explicit PASS/FAIL/NOT RUN.

The target-marker gate fix only rejects false-green probe behavior; it does not supply the missing runtimes. No production release is justified until the ledger has end-to-end evidence.


## Source implementation update — 2026-10-22

A first executable archive-validation layer has been added to the mirrored Koronos source and build script on this branch:

- `vendor/chimera-ii-os/source/kernel/include/chimera/initramfs_cpio.h` defines a bounded validation API with explicit error codes.
- `vendor/chimera-ii-os/source/kernel/core/initramfs_cpio.cpp` validates raw `070701`/`070702` newc headers, fixed-width hex fields, bounds, alignment, NUL-terminated names, absolute/traversal path rejection, entry types, CRC for `070702`, archive/entry/payload limits, and `TRAILER!!!`. Gzip is explicitly reported as unsupported compression rather than accepted on magic bytes alone.
- `vendor/chimera-ii-os/source/kernel/tests/initramfs_cpio_test.cpp` adds host regression cases; `build-koronos.sh` compiles/runs the tests and links the parser into Koronos.
- `vendor/chimera-ii-os/source/kernel/core/target_launch.cpp` calls the validator for Live/Recovery and requires a top-level `init` entry in raw archives. The existing target marker remains service-specific and generic native-init readiness cannot satisfy it.

This is partial archive validation only: there is no extraction, VFS mount, process-owned descriptor table, exec/wait/reap lifecycle, or target-service implementation yet. Duplicate/conflicting archive paths are not yet detected. Gzip/DEFLATE decompression remains absent and compressed production payloads fail closed. CI workflows triggered by the commits were queued/pending at the last poll; no passing build/test result is claimed.
