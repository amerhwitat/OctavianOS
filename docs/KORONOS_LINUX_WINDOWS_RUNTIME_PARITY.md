# Koronos runtime parity: Linux and Windows reference matrix

Status: design and acceptance matrix, not a claim of parity or release readiness. Applies to ChimeraIIOS and OctavianOS's vendored Chimera source as integrated by Koronos.

## Executive comparison

Linux and Windows are mature operating systems with complete process, virtual-memory, syscall, I/O, driver, security, scheduling, and service-management contracts. Koronos currently has useful foundations—ELF admission, an address-space binding record, a narrow native syscall path, target launch code, and VFS/filesystem components—but these are not yet a complete process runtime. Desktop assets, compatibility registries, source tests, and a ring-3 smoke payload must not be counted as an operational runtime subsystem.

Linux and Windows differ in ABI and internal architecture. Koronos should implement its own documented native ABI first, then implement compatibility layers at explicit boundaries. Do not copy Linux syscall numbers or assume POSIX semantics are automatically Windows-compatible.

## Component-by-component comparison

| Runtime contract | Linux reference | Windows reference | Koronos / Chimera evidence currently available | Required work and acceptance |
|---|---|---|---|---|
| User/kernel isolation | Per-process address spaces, user-copy checks, syscall entry/return, page-fault handling | User/kernel modes, private process address spaces and handle tables | ELF admission and a process runtime binding exist; candidate CPL3 smoke exists. Latest independent production verifier still fails to find the user-originated init syscall acknowledgement and actual init PID readiness. | Execute the exact production init ELF in a process-owned address space; validate mapped/unmapped pointers; record actual privilege transition and same PID in the trace. |
| Process/thread lifecycle | Task/process creation, scheduling, exit, wait/reap, signals | Process and thread objects, dispatcher/scheduler, waitable objects | Process records/PID allocation and bootstrap launch path exist; scheduler-owned context switching and general lifecycle are not proven. | Implement real task context switch, blocking/wakeup, parent/child status, wait/reap, cancellation and resource cleanup. Test multiple independently scheduled tasks. |
| Executable loading | ELF loading, VMAs, relocations as applicable, executable mappings | PE image loading, sections, imports and initialization contract | Koronos has bounded ELF admission and an ELF loader path. Chimera has PE inspection/loader components, but inspection/loader source does not establish Windows application compatibility. | Test malformed ELF and PE files, relocations/imports, stack/entry, NX/W^X, mapping failures and teardown. Define supported executable profiles explicitly. |
| Syscalls and user API | Stable Linux syscall ABI and libc-facing behavior | Native system services plus Win32/NT interfaces and subsystem translation | Native GETPID/TIME_TICKS/console WRITE are narrow; YIELD has been a no-op in the observed implementation. READ, file syscalls, fork/exec/wait, mmap/munmap and nanosleep are missing or incomplete. | Implement documented native syscall contracts with errno behavior; add native libc/sysroot. Keep unsupported calls fail-closed with ENOSYS, invalid pointers EFAULT and invalid descriptors EBADF. |
| File I/O and VFS | VFS, file descriptors, path lookup, mounts, per-file offsets and filesystem operations | I/O manager, object/handle model, layered IRP routing to filesystem/device drivers | ISO9660 and RAM-VFS components exist, but production init has not demonstrated a mounted root and per-process descriptor table end to end. | Extract bounded CPIO into a real mounted VFS before init; implement process-owned descriptors and OPEN/READ/WRITE/CLOSE, offsets, permissions and writable /tmp. Test actual ring-3 calls. |
| Drivers and devices | Device model, block/char interfaces, subsystem-specific drivers | PnP/power managers, device objects, I/O manager and layered drivers | Driver and device components exist in source; full production boot-to-userspace device path is not proven. | Define one coherent device-object/request contract, device discovery/lifecycle, error propagation, and test block, console, keyboard, pointer and display paths. |
| Service supervision | PID 1/init plus userspace service manager; services can remain running and be monitored | Service Control Manager and service processes with status/control contracts | Target readiness is currently a bootstrap marker, not proof of a persistent supervisor or healthy services. | Launch real service executables, monitor state/health, handle dependencies/restarts and child reaping. Require a live Aurora or Marine session process and display/input health. |
| Security and handles | Credentials, capabilities/permissions, LSM hooks, namespaces and resource limits | Access tokens, object ACLs, handle rights, security reference monitor and process isolation | ELF W^X and user-range validation are partial protections; a complete per-process security/handle model is not established by the inspected evidence. | Add permission checks at every object boundary, handle ownership/rights, process credentials, resource limits, and negative tests for cross-process access. |
| Memory management | VMAs, page faults, demand paging, reclaim, mapping and page-cache coherence | Per-process virtual address spaces, working sets, paging, section objects | Page-table and loader components exist; general process switching, recoverable user faults and memory pressure behavior need proof. | Test address-space switch/restore, user fault containment, map/unmap, guard pages, stack growth policy, page reclamation and mapping teardown. |
| SMP and synchronization | AP bring-up, per-CPU state, preemption, scheduler and synchronization primitives | Multiprocessor kernel scheduling, interrupts, dispatcher objects and synchronization | Prior scheduler parallel reporting was a serial loop; candidate smoke does not establish SMP. | Bring up two or more actual APs; prove overlapping execution on distinct CPU IDs with time windows, per-CPU state and lock stress. |
| Linux compatibility | Linux ABI, ELF/Linux loader, libc, procfs, pipes, signals, sockets, mmap and wait | Not native Windows behavior; a separate compatibility layer is needed | Command/syscall registries are not a complete Linux userspace environment. | Publish an explicit supported ABI matrix and tests for static/dynamic programs, libc, shell/coreutils, procfs, pipes, signals, sockets and process lifecycle. |
| Windows compatibility | Not native Linux behavior; a separate compatibility layer is needed | PE/COFF loader, Win32 APIs, NT object/handle semantics, I/O and service contracts | PE inspection/loader and Windows compatibility registries exist; they do not prove a working Win32 subsystem or broad application compatibility. | Define supported PE architectures and APIs; implement loader imports/relocations, Win32 API subset, handles, synchronization, file I/O and GUI boundaries; run real test binaries. |
| Installer and recovery | Filesystem/block operations with durable storage and repair tools | Storage stack, filesystem and recovery environment | Installer/recovery target definitions and boot smoke exist; durable install and recovery postconditions are not established. | Installer must write to a disposable disk and survive cold reboot; recovery must repair a seeded fault and verify the postcondition. |
| GUI/session runtime | Display/input stack and user-space compositor/session, applications | Windowing/graphics subsystem and user-mode applications/services | Aurora/Marine assets and target definitions exist; artwork and menu source are not session health. | Launch the real compositor/session, verify display frames, input events, app launch and clean shutdown; require the Live target readiness marker from the live session process. |

## Release gate and current CI interpretation

Latest inspected PR #135 head: dc266bbb8b6073c296bc855001bf249594190183.

- The native Koronos build job completed successfully.
- The independent Verify real Live, Installer, and Recovery userspace job failed for all three target traces with: missing user-originated init syscall acknowledgement (CPL 3), actual init PID readiness marker.
- The separate six-case candidate ring-3 launch smoke passed, but its own log says production payload acceptance remains separate; some UEFI logs also report missing matching OVMF code/vars images.
- Therefore these runs do not prove production init readiness, full userspace parity, all six production target/firmware combinations, durable install, recovery repair, GUI health or SMP.

Do not merge or publish while these failures remain. Do not weaken the verifier or print readiness markers from the kernel/bootstrap on behalf of a process. A passing acceptance trace must come from the exact production ELF launched from the immutable candidate ISO, and all artifact hashes must match.

## Prioritized implementation order

1. P0 — Production evidence and init identity: fix the production trace root cause, prove exact ELF hash and genuine CPL3 syscall with same PID, then run each target/firmware case independently.
2. P0 — Rootfs/VFS: bounded CPIO extraction, mount root, /dev, /proc, writable /tmp, process-owned descriptors, real OPEN/READ/WRITE/CLOSE.
3. P0 — Process runtime: architecture context switch, fault containment, exit/wait/reap, task states, scheduling and resource teardown.
4. P1 — Supervisor/services: persistent init/service manager, dependencies and health checks; Aurora/Marine live session health.
5. P1 — Installer/recovery: cold-reboot persistence and recovery repair postcondition on disposable test media.
6. P1 — ABI/compatibility: native libc/sysroot first; explicit Linux and Windows API support matrices and executable tests.
7. P2 — SMP: AP startup and overlapping execution on at least two CPUs.
8. Release: immutable ISO SHA-256, production ELF SHA-256, all six production traces, all postconditions and clean mandatory workflows. Publish only after all gates pass.

## Reference documentation

- Linux VFS contract: https://github.com/torvalds/linux/blob/master/Documentation/filesystems/vfs.rst
- Windows user/kernel isolation: https://learn.microsoft.com/windows-hardware/drivers/gettingstarted/user-mode-and-kernel-mode
- Windows virtual address spaces: https://learn.microsoft.com/en-us/windows-hardware/drivers/gettingstarted/virtual-address-spaces
- Windows I/O manager and layered driver requests: https://learn.microsoft.com/en-us/windows-hardware/drivers/kernel/overview-of-the-windows-i-o-model
- Windows kernel-mode managers: https://learn.microsoft.com/en-us/windows-hardware/drivers/kernel/