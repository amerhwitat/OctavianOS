# Koronos versus Linux kernel: userspace runtime gap analysis

Status: implementation plan and evidence ledger. This document is not a claim that the listed missing runtime features are complete.

## Architectural comparison

| Contract | Linux kernel reference behavior | Koronos observed in the current source | Required completion / evidence |
|---|---|---|---|
| Process creation | A process/task has kernel-owned lifecycle state, credentials, resources, execution context, and exit/wait semantics. | `process.cpp` admits an ELF and records PID/state/segments; this branch now binds the loaded address-space/root/entry/stack to that PID before allowing RUNNING and unbinds it before reclamation. `target_launch.cpp` still runs only the bootstrap init synchronously and tears down the address space when that invocation returns. | The PID-to-address-space binding is now explicit; next implement scheduler-owned context switching, parent/child relationships, wait/reap, and supervised long-lived tasks. |
| Address spaces | Per-process page tables, user/supervisor permissions, fault handling, switching, and memory-copy validation. | Koronos has a page-table backend, ELF loader, NX checks, and range validation. Only the selected bootstrap init is active; general context switching and fault-to-process lifecycle still need runtime proof. | Bind loaded image to process record; verify CR3/context switch and recoverable page-fault behavior. Validate every user pointer/range before kernel dereference. |
| Syscalls | Architecture entry preserves/validates context; dispatches implemented operations; returns standard errors; user pointers are copied/validated. | Native path implements GETPID, YIELD (currently a no-op), TIME_TICKS, WRITE to console, EXIT. READ, filesystem operations, fork/exec/wait, mmap/munmap, ioctl and nanosleep remain unsupported or incomplete. | Implement each syscall only when backed by a real subsystem and tests; unsupported calls must return ENOSYS, bad ranges EFAULT, invalid descriptors EBADF. |
| Filesystem / VFS | VFS abstracts files, directories, mounts, permissions, descriptors, and filesystem drivers. | Separate ISO9660/RAM-VFS work exists, but production init's executable runtime is not yet proven to have a mounted root, descriptor table, and working read/write paths. | Connect CPIO/rootfs extraction to mounted VFS; per-process fd table; validated OPEN/READ/WRITE/CLOSE and writable /tmp; test error cases and boundary lengths. |
| Init/service supervision | PID 1 supervises services, reaps children, handles failures, and establishes target-level readiness. | Current launch path starts one init image and expects a readiness string, then expects that process to exit cleanly. This is a bootstrap handshake, not a persistent service manager. | Add supervisor, child lifecycle/reaping/restart policy, service dependency states, and distinct Live/Desktop, Installer, and Recovery postconditions. |
| Desktop | User processes, graphics stack/compositor, input, display output, and session lifetime are independently observable. | An init readiness string is not proof that Aurora/Marine is alive or displaying frames. | Require a supervised compositor/session process, display-health/frame evidence, input path, and the Live-specific `USERSPACE TARGET READY: live component=aurora-session` marker from a real process. |
| Installer/recovery | Real block-device/filesystem operations with safety checks, durable writes, and repair invariants. | Boot/init readiness alone does not prove install persistence or recovery repair. | Cold reboot persistence test and recovery before/after invariant test on disposable images/devices. |
| SMP | APs start independently and execute concurrently; locking/interrupt state and CPU-local state are correct. | Scheduler's old `run_parallel` implementation serially called `run_once`; this is not SMP. | Keep parallel reporting fail-closed until AP startup is real; prove overlapping critical-section-safe work on two distinct online CPUs with timestamps/CPU IDs. |

## Changes made in this branch

1. Align the kernel's readiness-string parser with the acceptance verifier's ABI: `USERSPACE READY: target=<target> init_pid=<pid>`. The old parser expected `USERSPACE READY: <target> init pid=<pid>`, which did not match the verifier.
2. Bind the loaded production ELF's address-space object, CR3 root, entry point, and stack to its admitted PID before setting `RUNNING`; reject `RUNNING` if no runtime is bound, and unbind before address-space reclamation.
3. Validate the complete native `WRITE` user range against the active process address space before calling the console backend. Invalid/unmapped ranges return `-EFAULT` (`-14`).
4. Add regression tests for process/address-space binding order, readiness ABI, and range validation before reading user memory.

These changes fix two concrete interface/safety defects; they do **not** implement the remaining syscall set, VFS descriptor layer, process scheduler/context switching, service supervision, GUI runtime, installer/recovery semantics, or SMP.

## Linux reference points

Use Linux's stable conceptual boundaries as design references: architecture syscall entry; process/task lifecycle; MM/address-space management; user-copy and access checks; VFS/file-descriptor abstraction; device/block layers; init/service supervision; and SMP/AP lifecycle. Do not transplant Linux implementation files without their dependencies or treat Linux ABI numbers as Koronos' native ABI. Implement the kernel contracts first, then compatibility translation at the boundary.

## Release gate: all required

- [ ] Exact immutable ISO SHA-256 is recorded for every Live/Installer/Recovery × BIOS/UEFI case.
- [ ] Production ELF hash matches the artifact actually launched.
- [ ] Kernel-ready → CPL3 user-originated syscall → same nonzero init PID → target readiness, all ordered and from the production trace.
- [ ] Process owns a real loaded address space; syscall READ/WRITE/OPEN/CLOSE are tested against mapped and unmapped buffers.
- [ ] fork/exec/wait (or an explicitly documented supported process model) and child reaping are tested.
- [ ] Live supervisor proves Aurora session and display health; Installer performs a durable write and passes cold reboot; Recovery proves a repair postcondition.
- [ ] At least two CPUs are online from actual AP startup and show overlapping execution.
- [ ] All six immutable-ISO cases and all relevant postcondition tests pass. Publication remains blocked until then.
