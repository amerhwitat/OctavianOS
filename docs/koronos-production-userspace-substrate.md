# Koronos production userspace substrate — implementation plan

**Status: first substrate slice committed; production acceptance remains incomplete.** The code now includes a bounded read-only CPIO `newc` parser, hosted adversarial parser tests, process-owned read-only descriptor helpers, and explicit exit-status/reap-once metadata. These are not yet wired into a safe user syscall ABI or a blocking scheduler wait path. Do not use this as evidence that PID 1, a service supervisor, Linux syscall layer, or graphical userspace is operational.

## Root cause

The canonical production verifier is correctly failing closed. The current `native_init.c` performs ring-3/syscall/PID/console smoke checks, prints `NATIVE INIT BLOCKED`, and exits with status 78. `service.cpp` validates dependency metadata and tracks service states; it does not launch processes or execute service backends. The native syscall dispatcher has a narrow smoke-test surface and lacks the file and process operations required for a usable PID 1.

This is an operating-system substrate gap, not a readiness-marker or verifier defect. Do not remove the blocked diagnostic, weaken the gate, or emit readiness based on a registry state alone.

## Linux model compared with Koronos requirements

| Subsystem | Linux model | Koronos requirement |
|---|---|---|
| Filesystem / VFS | Initramfs rootfs, VFS path and inode operations, file descriptors; additional pseudo-filesystems such as procfs/sysfs/devtmpfs | Validated read-only CPIO `newc` archive reader, normalized paths, bounded lookup/read, per-process descriptor table, correct errors; mount and device filesystems only when implemented |
| Process lifecycle | Exit/reap, parent-child wait, fork/exec, memory/file cleanup and wakeups | Kernel-owned task identity and exit status, wait queues, wakeups, descriptor cleanup, address-space lifetime rules; do not expose fork/exec until implemented |
| Service supervision | PID 1 launches services, follows dependencies, performs health checks, observes exits and propagates failures | Real executable service backends, dependency-ordered startup, bounded health checks and failure propagation; service registry state is not proof of execution |
| Syscall ABI | ABI-specific entry, validated user memory, stable errno and operation semantics | Native ABI contract and per-process personality, validated copyin/copyout, implemented backend per advertised syscall, regression tests |
| Device and graphics | Driver model plus userspace policy/services | Real device discovery and storage/display/input APIs, compositor process and target-specific operational checks |

## Pillar 1 — bounded initramfs CPIO VFS

Implement this in a dedicated kernel module (suggested path: `kernel/core/vfs_cpio.cpp`) and expose a narrow header only after the contracts and tests are defined.

Requirements:
- Accept a boot-module byte range only after overflow-safe bounds checks; never trust a raw pointer or archive size.
- Parse CPIO `newc` (`070701`) fields with a freestanding hexadecimal parser. Do not use `sscanf`, unbounded string routines, or assume fields are NUL-terminated.
- Check the 110-byte header, nonzero bounded `namesize`, terminating NUL, 4-byte alignment arithmetic, file-data bounds, file-size bounds, and trailer handling before dereferencing.
- Validate archive traversal monotonicity and reject overflow, truncation, malformed magic, duplicate/ambiguous normalized paths, unsupported entry types, and path traversal (`..`); normalize a single leading slash consistently.
- Expose read-only lookup/read semantics first. Return explicit status codes distinct from a zero-length file; never return an unvalidated pointer as a user-accessible address.
- Keep archive memory immutable and alive for every returned file view; document lifetime ownership.
- Add hosted adversarial tests for truncated headers/data, integer overflow, missing NUL, invalid alignment, malformed hex, duplicate paths, traversal, trailer, empty files and valid multi-entry archives. Add fuzzing where the project toolchain supports it.

Do not integrate `open`/`read` into the syscall dispatcher until user-pointer validation, process identity, descriptor ownership, and error translation are in place. A parser-only unit test is not proof that PID 1 can use the VFS.

## Pillar 2 — process and syscall substrate

- Bind every syscall to the actual active task and ABI personality. Validate user buffers and strings against the active address space before access.
- Implement a process-owned descriptor table with explicit ownership/refcounting and defined close-on-exit behavior; initially support only read-only regular files from the validated CPIO archive.
- Implement native `open`-equivalent and `read` semantics with a documented native syscall ABI. Do not confuse host Linux syscall numbers with Koronos canonical syscall IDs.
- Implement exit status storage, safe teardown, parent-child relationships, blocking/waking wait semantics, and reap-once behavior before advertising wait operations.
- Keep `fork` and `execve` returning the defined unsupported error until genuine process creation and ELF replacement are implemented and tested.
- Preserve fail-closed behavior for unknown calls, invalid pointers, invalid descriptors, unsupported flags, and ABI/entry mismatches.
- Add host-side tests for permission errors, EOF, short reads, invalid descriptors, boundary pointers, exit/wait races, double reap, and cleanup. Then exercise the same paths in a booted guest.

## Pillar 3 — executable service supervision

Refactor the service registry only after real backend contracts exist. Each service descriptor needs an initialization/start operation, a health-check operation, and explicit failure/stop behavior. Startup must respect the dependency graph, detect cycles, enforce timeouts, and mark a service RUNNING only after the backend reports healthy. The supervisor must observe real task/process status, not merely an initialization function returning zero.

Start with the VFS backend and the minimal process/console foundation. Device/storage/security/logging and compositor services must remain BLOCKED until their backends exist. Aurora must not be reported ready merely because its assets are packaged. Installer readiness requires actual storage validation, a safe disposable-disk write, and a successful installed reboot; recovery readiness requires a real recovery operation.

## Important ABI correction to the supplied sketch

The proposed example uses `syscall(15)` as `KORE_SYS_CHECK_SERVICES`, but the current `chimera/syscall.h` defines canonical syscall 15 as `CHM_SYS_ARCH_PRCTL`. Reusing 15 for service health would silently collide with an existing ABI contract. Add a new explicitly versioned syscall only if kernel/user API design proves it necessary; preferably expose health to a privileged supervisor through a designed IPC/control interface. Do not copy the illustrative snippets directly into production: they omit bounds checks, backend implementations, process context, and error semantics.

Similarly, a CPIO parser must parse each hexadecimal field and validate every offset before forming/dereferencing pointers. A three-entry service loop is only a structural sketch until its init hooks are actual implementations with health checks. A userspace readiness line must only be emitted after the target's real final destination is operating.

## Acceptance sequence

1. CPIO parser + adversarial host tests pass.
2. Read-only VFS lookup/read is reachable through a process-owned descriptor table with safe user-memory access.
3. Native process exit/wait/reap and cleanup tests pass; unsupported process calls remain unavailable.
4. Real service processes start in dependency order and report health through observable checks.
5. Booted Live/Installer/Recovery tests pass under both BIOS and UEFI (six cases), including Aurora, install-to-disposable-disk and reboot, and recovery repair.
6. AP startup, per-CPU scheduler operation and cross-CPU synchronization are demonstrated under genuine SMP.

## Release policy

Production acceptance remains **FAIL** and prerelease publication remains blocked until the full six-case matrix and the additional end-to-end checks above pass. Ring-3 probes, ELF structural validation, a compiled kernel, registry entries, packaged assets, or a readiness-shaped log line are not substitutes for this evidence.


## Implementation slice committed (2026-10-20)

The current branch now contains the first code slice:

- `kernel/core/vfs_cpio.cpp` and `kernel/include/chimera/vfs_cpio.h`: bounded `070701` reader (CRC variant `070702` is rejected until its checksum is verified), overflow-checked offsets and alignment, bounded hexadecimal fields and names, normalized absolute/relative paths, traversal/duplicate rejection, trailer requirement, regular-file read views, and range-checked partial reads. It intentionally rejects unsupported entry types rather than pretending to implement symlink/device semantics. Archive storage remains owned by the boot module and must outlive every view.
- `kernel/tests/vfs_cpio_test.cpp`: hosted cases for valid lookup/read, EOF, missing paths, truncation, duplicate paths, traversal and malformed magic.
- `kernel/core/process.cpp` / `kernel/include/chimera/process.h`: process-owned descriptor slots for read-only CPIO files, sequential reads, close, exit status, parent association, and reap-once polling. Process ABI is versioned to 2 because the process record grew.
- `kernel/tests/process_lifecycle_test.cpp`: lifecycle and descriptor tests, including exit-time descriptor cleanup.
- `kernel/build-koronos.sh`: adds the new source and runs both hosted regression executables before the freestanding build.

Important boundaries still outstanding:
- `chimera_process_waitpid_poll` is explicitly **non-blocking**. It does not park a task, register a wait queue, or perform scheduler wakeups.
- Process table mutations are not yet integrated with a kernel-wide SMP-safe process lock or a scheduler-owned task lifetime. Do not treat this metadata table as a complete concurrent process manager.
- Descriptor helpers accept kernel buffers and kernel path strings. They are not user-pointer-safe syscall entry points; `open`/`read`/close are not exposed to ring 3, and the archive is not yet mounted/selected from the live target's initramfs.
- Address-space destruction, process record teardown, descriptor cleanup, and the user-entry return path still need one coordinated ownership contract before `waitpid`, `fork`, or `execve` can be advertised.
- The new hosted tests are wired into the standard build script, but this commit has not yet produced a verified CI run or booted-guest result.

Therefore the canonical production userspace gate stays **FAIL**. Do not modify the gate or let these unit-level additions emit readiness. Continue with user-memory copyin/copyout and active-initramfs binding, then a scheduler-integrated process/wait lifecycle and real service backends.
