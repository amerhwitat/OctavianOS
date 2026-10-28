# Koronos vs. Linux kernel: runtime integration gap analysis

This is an evidence-led engineering comparison, not a claim of Linux feature parity.

## Linux reference architecture

Linux separates task/process lifecycle, virtual memory/address-space ownership, syscall entry and user-memory access, VFS file descriptors and filesystem operations, init/service supervision, device/storage operations, and AP/SMP scheduling. Its VFS file objects are attached to a process file-descriptor table and route reads/writes through filesystem-specific operations; its memory manager tracks valid user ranges in a per-address-space structure. See the official kernel docs:
- https://docs.kernel.org/filesystems/vfs.html
- https://docs.kernel.org/mm/process_addrs.html

Koronos should implement those contracts in its own architecture and native ABI, not transplant Linux internal source files or claim compatibility because syscall names overlap.

## Current Koronos capabilities in the VFS-syscall branch

- A bounded CPIO archive reader/mount path and read-only target-root mount are present.
- The native syscall dispatcher has OPEN (read-only), READ, CLOSE, SEEK, WRITE, GETPID, YIELD, TIME_TICKS, and EXIT handling. OPEN and READ use the active process descriptor state; read destination and pathname ranges are validated. FORK, EXECVE, and WAITPID are explicitly unavailable because resumable contexts, address-space ownership transfer, and full scheduling/reaping are not yet integrated.
- ELF loading creates a real address-space object and CR3 root; the launch path enters ring 3 synchronously with a bounded kernel timeout.
- This change binds the loaded address-space object, root, entry point, and stack to the admitted PID before allowing the process state to become RUNNING. It unbinds the runtime before page-table reclamation and prevents state exit/reap while a runtime binding remains live.
- ELF admission now validates the program-header table bounds and requires an executable entry segment.
- Native console WRITE now validates the complete user buffer range against the active address space before dereferencing it.
- SEEK now uses per-process descriptor offsets, validates whence, handles signed offsets without overflow, and rejects invalid descriptors.
- The ring-3 acceptance probe, kernel marker parser, workflow grep, and verifier share the USERSPACE READY: target=<target> init_pid=<pid> format. Probe-only success remains explicitly distinct from production acceptance.

## Gaps still blocking production readiness

| Area | Remaining implementation/evidence |
|---|---|
| Process execution | Scheduler-owned resumable CPU contexts, real context switches between address spaces, signal/fault delivery or process termination, parent/child creation and robust wait/reap. Existing waitpid polling is lifecycle metadata, not scheduler sleep/wakeup. |
| Filesystem | VFS-backed write/create for writable /tmp; descriptor dup/stat/permissions; robust copy-from/copy-to-user primitives that handle faults and concurrent map changes; actual rootfs extraction and mount semantics for production payloads. Current CPIO root is read-only. |
| Supervision | Persistent PID 1/service manager with dependencies, exit/reap/restart policies, and independently observable Live, Installer, Recovery services. Current target launch executes one init synchronously and then tears down its address space. |
| Aurora / Marine | Real supervised session/compositor, frame/display health, input path, and USERSPACE TARGET READY: live component=aurora-session emitted only after actual component health. A readiness string alone is not a desktop. |
| Installer | Actual block-device write transaction, fsync/flush semantics, cold reboot, and persistent post-reboot verification. |
| Recovery | Repair operations with captured before/after invariants proving the repair effect. |
| SMP | AP startup and per-CPU execution with real overlapping work on at least two CPUs. Serial stepping must never be labelled parallel. |
| Release evidence | Exact immutable ISO SHA-256 and production init ELF hash for all six Live/Installer/Recovery × BIOS/UEFI cases; ordered kernel-ready → CPL3 syscall acknowledgement → matching nonzero PID → target-specific readiness; all postcondition tests green. |

## Release policy

Do not merge or publish on the strength of source presence, compile-only checks, or ring-3 candidate probes. Keep publication blocked until the six immutable-ISO production traces, desktop health, cold-reboot persistence, recovery repair, and two-CPU overlap evidence pass.

## Latest execution evidence (2026-10-28)

The latest PR validation for commit `677229acf040f1a76dbf5c857dd71a03ad0e1626` is not a production pass:

- Source integration and boot-target routing contract workflows passed.
- The native Koronos build job completed successfully, but its downstream **Verify real Live, Installer, and Recovery userspace** job failed.
- The verifier reported `FAIL: missing production service readiness (init explicitly reported NATIVE INIT BLOCKED)` for all six target/firmware traces. The prerelease/publish job was skipped by the fail-closed gate.
- The candidate ring-3 probe matrix is a separate workflow and is explicitly not production acceptance.

This is a runtime/service-availability failure, not a reason to weaken the verifier or synthesize readiness. The next implementation step is to identify and satisfy each concrete `NATIVE INIT BLOCKED` prerequisite in the production init path, then rerun the immutable full-ISO matrix. Do not mark item 1 complete merely because an ELF can be loaded and entered in ring 3: the production archive's actual `/init` must execute through a supported ELF/interpreter path and the target service manager must reach its real postconditions.

## Required acceptance matrix

For each of Live, Installer, and Recovery under both BIOS and UEFI, retain a trace tied to the exact ISO SHA-256 and production init ELF SHA-256. The trace must show, in order: kernel ready; CPL3-originated syscall acknowledgement; matching nonzero native-init PID; target readiness emitted by the running init; and target-specific postconditions. Add independent evidence for Aurora/Marine session health, installer cold-reboot persistence, recovery repair invariants, and AP overlap on at least two CPUs. Missing artifacts, missing markers, timeout, nonzero init exit, or any unmeasured postcondition must fail closed.

## Concrete root cause of the six-case readiness failure (2026-10-28)

The production failure is deterministic in the current source, not an unexplained QEMU issue. `vendor/chimera-ii-os/source/kernel/userspace/native_init.c` validates `/etc/chimera/target`, emits `NATIVE INIT ROOTFS VERIFIED`, then unconditionally emits `NATIVE INIT BLOCKED` and exits with status 78. This is an intentional fail-closed stub. Changing the message alone cannot make the production gate pass, and removing the unconditional block or emitting readiness without real services would be a false positive.

The blocker message now names the actual unavailable capabilities: scheduler-owned resumable process contexts; `FORK`, `EXECVE`, and blocking `WAITPID`; writable filesystem backend; and native storage, security, logging, graphics service providers. The syscall ABI regression test now asserts these limitations remain explicit and that unsupported process syscalls stay `ENOSYS`.

This change improves diagnosability and regression protection only. It does **not** implement the listed services or complete production acceptance. The next implementation must supply real backends and a supervised service startup path, with service-specific success/failure results and actual target postconditions. Keep the release gate red until the production archive's actual `/init` can reach those postconditions.
