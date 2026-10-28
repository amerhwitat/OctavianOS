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


## Execution update (2026-10-28, commit `ceffea5e8660623232b2bfcf39427be8adca757c`)

Latest workflow evidence supersedes the earlier run references above:

- [Native Koronos kernel build, run 40712518035](https://github.com/amerhwitat/OctavianOS/actions/runs/40712518035): the `build-koronos` job passed, including freestanding ELF/Multiboot2 checks, QEMU kernel smoke, target payload staging, candidate ISO generation, and target-routing smoke tests. Its separate **Verify real Live, Installer, and Recovery userspace** job failed.
- The verifier downloaded the full-ISO trace artifact and failed all six cases—Live, Installer, Recovery × BIOS, UEFI—with `FAIL: missing production service readiness (init explicitly reported NATIVE INIT BLOCKED)`. The prerelease job was skipped. This confirms that the diagnostic change is present and the production service gap remains; it is not a release pass.
- [Koronos Ring-3 Probe Matrix, run 40712518033](https://github.com/amerhwitat/OctavianOS/actions/runs/40712518033): all six *non-production candidate* jobs passed. This is useful runtime-probe evidence only and does not supersede the failed full-ISO production verifier.
- [OctavianOS Chimera source integration, run 40712518178](https://github.com/amerhwitat/OctavianOS/actions/runs/40712518178) and [boot target routing contracts, run 40712518182](https://github.com/amerhwitat/OctavianOS/actions/runs/40712518182) passed their scoped checks.

### Updated release disposition

| Requirement | Evidence-backed status |
|---|---|
| Identify unconditional production-init block | Confirmed in `native_init.c` after target-root validation |
| Blocker diagnostics and ABI regression guard | Committed; scoped workflows pass |
| Supported execution of production archive `/init` through real service runtime | Incomplete; init still exits 78 |
| Scheduler-owned resumable contexts and real `FORK` / `EXECVE` / blocking `WAITPID` | Incomplete; these syscalls still return `ENOSYS` |
| Writable storage/filesystem and supervised target services | Incomplete; current syscall VFS path is read-only CPIO |
| Aurora/Marine session and display-health evidence | Unproven |
| Installer cold-reboot persistence and recovery repair postconditions | Unproven; existing tests are routing smoke tests, not write/repair proof |
| AP startup and overlapping execution on at least two CPUs | Unproven |
| Six immutable production ISO cases with exact hashes and ordered evidence | Blocked; latest full-ISO verifier failed all six cases |
| Merge/publication | Blocked; PR remains draft and prerelease job was skipped |

### Next implementation dependency order

Do not delete the fail-closed exit or add readiness output to bypass the verifier. Implement and test these dependencies in order: (1) scheduler-owned saved CPU context plus safe address-space switch and preemption/yield; (2) process create/exec, exit cleanup, parent/child relationship and scheduler-integrated wait block/wakeup/reap; (3) fault-safe user-copy and VFS mount/namespace with writable tmpfs and descriptor operations; (4) production ELF/interpreter and initramfs extraction path; (5) PID 1 service registry/supervisor that launches target-specific services and observes their real exit/health state; (6) display/session health, installer durable-write/cold-boot test, recovery before/after invariants, and AP overlap instrumentation. Rebuild the immutable ISO only after these facilities exist, then rerun the six-case matrix and independent postcondition tests. Any missing capability must continue to fail closed.


## Linux and Windows userspace parity comparison (2026-10-28)

This is an implementation gap analysis, not a claim that Koronos is Linux- or Windows-compatible. Linux is the POSIX/syscall and filesystem reference; Windows is the process/thread/handle/service reference. Do not conflate their APIs: implement a stable Koronos native ABI first, then explicit compatibility layers with documented semantics.

### Evidence-based subsystem matrix

| Subsystem | Linux reference behavior | Windows reference behavior | Current Koronos/Chimera evidence | Required implementation and acceptance |
|---|---|---|---|---|
| Process/thread execution | A process has an address space and threads; `fork` creates a child and `execve` replaces the current program image. `waitpid` can wait for child state changes. | A process owns a virtual address space and handles; a thread has its own saved machine context and is the scheduling unit. `CreateProcess` creates a process and primary thread. | ELF admission and address-space primitives exist, but process admission alone is not execution. `FORK`, `EXECVE`, `WAITPID` are explicitly unavailable; scheduler callbacks return before applying actions. | Scheduler-owned resumable register/stack contexts; validated address-space switch; child/parent ownership; transactional exec (do not destroy old image until new image is fully admitted); blocking wait queue; exit status, signal/fault path and single-owner reap. Test child isolation, failed exec rollback, blocked parent wakeup, zombie/reap, invalid pointers and repeated lifecycle. |
| Scheduling and SMP | Kernel schedules runnable threads preemptively; separate CPUs may execute distinct runnable threads concurrently. | Windows uses preemptive thread scheduling; multiprocessor systems may execute threads simultaneously. | Current scheduler callback runner is cooperative. `chimera_sched_run_parallel` returns zero, explicitly fail-closed; serial range dispatch is not SMP. | Save/restore all ABI-required registers and flags on interrupt/yield; timer-driven preemption; per-CPU current task and run queues; AP startup and online acknowledgement; inter-CPU synchronization/IPI; overlapping critical-section-free workload on at least two CPUs with per-CPU counters/timestamps. |
| Filesystem and descriptors | File descriptors reference open file descriptions; `open/read/write/lseek/close` have defined access/error semantics; mount namespaces scope visible mounts. | Win32 applications generally access kernel objects and files through handles; access checks and handle lifetime are explicit. | CPIO archive validation and read-only root mount exist; current init opens `/etc/chimera/target` read-only. No production writable filesystem backend is established. | VFS inode/dentry/mount abstraction; per-process descriptor table and refcounts; checked user-copy; writable tmpfs with create/write/truncate/rename/unlink/mkdir; sync/flush and block-device persistence backend; access modes and errno mapping. Test descriptor inheritance/close-on-exec policy, boundary and invalid pointers, concurrent mutation, full media and crash/flush semantics. |
| Init/service supervision | Linux boot userspace normally launches PID 1/service manager, which starts and supervises services and receives process exit state. | Windows service control manager manages service lifecycle and service status; service processes are ordinary processes with defined control/reporting contracts. | Native init verifies target metadata and then deliberately emits `NATIVE INIT BLOCKED` and exits 78. No service readiness is proven. | PID 1 must load a target manifest, validate dependencies, spawn real service binaries, track PID/exit/health, enforce start deadlines and restart limits, propagate failure, and only declare target-ready after service-specific probes pass. Add fault injection for missing binary, dependency cycle, early exit and restart storm. |
| Security and isolation | Credentials, permission checks, capabilities/LSM hooks, namespaces, and syscall validation are part of process/file access semantics. | Access tokens, security descriptors, object access checks, process mitigations and job objects contribute to isolation/control. | User-range validation and per-process address-space binding exist in portions of the native path; a complete credential/permission/service security model is not evidenced. | Define UID/GID or equivalent principals, permission bits/ACL policy, inherited credentials, descriptor authorization, syscall audit, W^X/NX and user/kernel separation. Negative tests must prove unauthorized reads/writes/execs fail. |
| Device and I/O model | File/device nodes and driver APIs provide uniform operations; async I/O and polling mechanisms have established semantics. | I/O commonly uses handles, I/O completion mechanisms, and driver/device objects. | Kernel syscall path has console output and read-only CPIO operations; storage/security/logging/graphics service providers are explicitly named as unavailable. | Define device registry and capability-checked handles; block storage completion/error model; timer and wait primitives; input/display providers. Test timeout, device removal/failure and resource cleanup. |
| GUI/session | Linux desktop stacks typically separate display server/compositor, session manager, input and application processes. | Windows desktop/session/windowing services and USER/GDI APIs expose process-facing GUI primitives. | Aurora/Marine artwork and target routing are not evidence of a running session or functional display backend. | Implement a real graphics/input provider, session lifecycle, compositor connection, frame-present and input round-trip health checks; separate GUI health from kernel boot readiness. |
| Installation/recovery | Durable storage operations depend on filesystem/block-device correctness and sync ordering. | Installation and recovery likewise depend on storage APIs, volume management, and verifiable repair outcomes. | Existing installer/recovery routing smoke tests explicitly do not prove disk writes or repair. | Write a uniquely identified test record, flush all layers, cold reboot, and verify hash; for recovery capture a precondition, execute repair, reboot/remount and verify the postcondition plus preserved unrelated data. |

### Implementation rules

1. **Do not port Linux or Windows syscall numbers directly into the native ABI.** Preserve the existing Koronos syscall IDs; compatibility personalities must translate their own documented ABI at a boundary.
2. **Separate API compatibility from kernel capability.** A wrapper must return a truthful unsupported error until the underlying primitive exists; it must not emulate process creation by running callbacks serially.
3. **Use transactional state changes.** Address-space creation, ELF load, descriptor setup and process publication either complete atomically or roll back every allocation and binding.
4. **Make wait and I/O genuinely blocking.** A blocked task must retain its complete execution context and be awakened by a condition/event; a callback returning is not a suspended process.
5. **Treat filesystem persistence as a hardware path.** RAM-VFS success is not a disk durability claim. Require a real storage backend, flush/barrier contract, cold power cycle and re-read.
6. **Keep readiness semantic.** Kernel ready, ring-3 syscall proof, PID identity, rootfs mounted, service process alive, service health and desktop health are distinct postconditions.
7. **Keep release gating fail-closed.** Do not merge or publish until each target/firmware pair records the same real init PID, exact immutable ISO/init hashes, ordered evidence and independent target-specific postconditions.

### External reference documentation

- Linux `execve(2)`: https://man7.org/linux/man-pages/man2/execve.2.html
- Linux `waitpid(2)`: https://man7.org/linux/man-pages/man2/waitpid.2.html
- Linux `fork(2)`: https://man7.org/linux/man-pages/man2/fork.2.html
- Linux `open(2)`: https://man7.org/linux/man-pages/man2/open.2.html
- Linux `mount(2)` and mount namespaces: https://man7.org/linux/man-pages/man2/mount.2.html
- Microsoft processes and threads: https://learn.microsoft.com/windows/win32/procthread/processes-and-threads
- Microsoft process/thread API reference: https://learn.microsoft.com/windows/win32/api/_processthreadsapi/
- Microsoft service applications: https://learn.microsoft.com/windows/win32/services/service-programs

The current production verifier remains the authoritative status for the candidate: all six production userspace cases failed because init explicitly blocked; a candidate probe pass does not change that result.


## Detailed userspace ABI parity matrix (source inspection, 2026-10-28)

This table describes the currently inspected implementation, not intended future behavior. Linux comparisons refer to the documented Linux userspace ABI; syscall numbers are ABI-specific and are not interchangeable.

| Userspace contract | Koronos source status | Linux userspace expectation | Release impact / required implementation |
|---|---|---|---|
| Process identity | Native `GETPID` reads the active kernel process record; the generic compatibility dispatcher rejects it without a process context | `getpid(2)` returns the caller's actual PID | Preserve a single authoritative process identity through context switches, fork, exec, and wait |
| User-origin proof | DPL3 `int 0x80` acknowledgement checks saved CS.RPL and validates active PID/CR3/RIP | Linux syscall entry records the calling task and user register frame | Keep the privilege-origin check; extend it to every task's saved trap frame instead of one global active process |
| Console output | `WRITE` supports fd 0..2 with a 4096-byte cap and address-space range validation | `write(2)` operates on process-owned descriptors and may write to arbitrary valid open objects | Add per-task descriptor-table ownership, partial writes, and backend errors; console-only writes are not a full file ABI |
| File open/read/close/seek | `OPEN` is read-only, `READ` and `CLOSE` use process records, `SEEK` uses per-process offsets; CPIO root is read-only | `open(2)`, `read(2)`, `close(2)`, `lseek(2)` use VFS objects, permissions and filesystem operations | Add writable filesystem operations, shared open-file-description semantics where required, permissions, path traversal policy, and storage-backed filesystems |
| User memory safety | Address ranges are checked against the current CR3; a bounded copy validates ranges before direct copy | Kernel user-copy paths must handle faults and mapping changes without trusting userspace pointers | Implement fault-safe copyin/copyout/pin-or-lock semantics and bind validation to the actual task address space |
| Yield/scheduling | Native `YIELD` returns `ENOSYS`; callback stepping is not a saved-context switch | `sched_yield(2)` yields the running task to the scheduler | Save/restore general registers, RFLAGS, RIP/RSP, privilege return state, FPU/SIMD state as enabled, kernel stack, and address-space root; only report success after a real scheduling transition |
| Fork/exec/wait | `FORK`, `EXECVE`, `WAITPID` return `ENOSYS` in the native dispatcher | `fork(2)`, `execve(2)`, `waitpid(2)` provide child creation, transactional image replacement, blocking notification and reaping | Implement copy-on-write or safe address-space clone, atomic exec commit/rollback, parent-child links, blocking sleep/wakeup, exit status and exactly-once reap |
| Exit lifecycle | Native exit returns a sentinel to the synchronous launcher; runtime is then unbound and address space reclaimed | `exit(2)` terminates a task; waitable child state survives until reaped | Route exit through scheduler/task lifecycle; do not reclaim a running stack/address space; retain zombie status until parent or init reaps |
| PID 1 / services | Native init verifies target metadata then explicitly exits 78 because service supervision and providers are absent | Linux PID 1 adopts orphans and supervises the system's service graph through userspace init/service manager | Implement a persistent init process, service dependency graph, restart/failure policy, reaping and independently tested health probes |
| Signals, pipes, sockets, polling, threads | No complete process runtime/IPC contract demonstrated by the inspected paths | Common Linux applications depend on signals, pipes, sockets, `poll/epoll`, futexes and threads | Track these as separate compatibility milestones; do not claim broad Linux userspace compatibility based on the small native syscall subset |
| Device and storage I/O | Production device/storage service providers are not available to native init | Linux exposes device operations through kernel drivers, block layer, VFS and userspace APIs | Provide real device drivers/service endpoints, write ordering and flush semantics before installer durability tests |
| Desktop session | No production-ready compositor/session health proof in the reviewed launch path | A desktop stack requires process supervision, IPC, device/input/display support and working graphics APIs | Require a running Aurora/Marine session plus external frame/input health evidence, not a log string alone |

### Runtime ownership and context-switch invariants

The present launch path in `target_launch.cpp` loads and binds one process, sets it RUNNING, calls `koronos_arch_enter_user()` synchronously, then unbinds and destroys the address space when that call returns. This is a bounded user-mode probe/launcher, not a scheduler-owned resumable task. The active target, PID, CR3 and acknowledgement flags are global single-process state, so they must not be treated as safe for concurrent tasks or SMP.

Before implementing `FORK/EXECVE/WAITPID`, the x86-64 entry path needs one documented trap-frame layout shared by syscall and interrupt assembly, a per-task kernel stack, saved user RIP/RSP/RFLAGS and callee/caller register state as required by the entry ABI, address-space root ownership, and a scheduler transition that can suspend task A and resume task B. CR3 changes must occur with the correct TLB/PCID rules, and FPU/SIMD state must be managed consistently with enabled CPU features. Interrupt return must restore a frame belonging to the selected task. A scheduler callback returning is not proof of any of these properties.

The current global active-process validation must become task-local. Every syscall must resolve its caller from the saved entry context, validate user pointers against that caller's address space, and operate on that caller's descriptor table. For SMP, scheduler/process state needs locking or per-CPU ownership rules; one global `active_pid` cannot represent two simultaneously running CPUs.

### Production acceptance sequence and evidence

For each immutable Live, Installer and Recovery ISO under BIOS and UEFI, require all of the following from the actual packaged init ELF and runtime:
1. Record ISO SHA-256 and extracted init ELF SHA-256 before boot.
2. Observe kernel readiness, then a DPL3-originated syscall acknowledgement from the production init PID.
3. Observe a nonzero PID obtained from the kernel process table and prove subsequent user syscalls resolve to that same task and CR3.
4. Exercise rootfs open/read/close and writable `/tmp`; test invalid pointers and descriptor isolation as negative cases.
5. Observe a real supervised PID 1 service graph and target-specific postconditions. Live must include independently measured Aurora/Marine session health; Installer must survive flush and cold reboot; Recovery must demonstrate a recorded before/after repair invariant.
6. Capture AP startup and overlapping work on at least two CPUs with per-CPU evidence.
7. Fail on any missing artifact, timeout, nonzero init exit, mismatch in hash/PID/order, unmeasured postcondition or synthetic marker. Candidate probes remain supplemental and cannot satisfy the production matrix.

### Explicit current disposition

The reviewed code still contains an intentional `NATIVE INIT BLOCKED` / exit-78 path. Do not remove it until the real service manager and required providers exist. The documentation update is an implementation plan and source-level parity assessment, not evidence that these runtime features have been implemented. Production acceptance and prerelease remain blocked.
