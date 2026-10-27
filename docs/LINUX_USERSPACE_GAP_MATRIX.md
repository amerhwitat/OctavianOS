# Linux userspace parity gap matrix — OctavianOS

**Scope:** OctavianOS's native Koronos path and its vendored ChimeraIIOS source compared with Linux's kernel-to-userspace contract. This document distinguishes vendored source, Octavian-specific integration, and runtime proof.

## Architecture comparison

OctavianOS vendors the ChimeraIIOS source under vendor/chimera-ii-os/source/, but the vendored code and Octavian's top-level release/target integration are separate layers. A fix to one layer must not be assumed to update the other. Linux is the behavioral reference; copying Linux implementation code directly is not the goal.

| Area | Linux contract | OctavianOS current evidence | Gap to close |
|---|---|---|---|
| Production init identity | Bootloader supplies root/init; kernel executes the selected init | Target payload contract and staged-init checks exist; Multiboot module classification is only identification | Bind selected Live/Installer/Recovery payload to exact production init ELF and verify hash/target end to end |
| Rootfs/VFS | Initramfs is unpacked into a usable root; VFS resolves paths and mounts | Rootfs validation and payload staging do not prove VFS publication in the running kernel | Add bounded CPIO extraction to kernel VFS, mount root before launch, validate required nodes and writable tmpfs |
| ELF + ring 3 | Process has isolated mappings, user stack, transition state and an executable entry | Vendored ELF loader maps through callbacks; Octavian has native user-entry/context code, but production target execution must be traced | Wire the exact staged init to the real loader, process-owned address space and architecture entry/return path |
| Syscall context | Syscalls use caller-owned PID, validated pointers and lifecycle state | Octavian native dispatcher checks syscall context and obtains active PID; compatibility dispatcher has no process context | Keep compat path fail-closed; demonstrate native ring-3 syscall path and same-PID readiness in QEMU |
| Exit/wait/supervision | Exit tears down a process; parent can wait/reap; init supervises children | Process/task records and some lifecycle bookkeeping exist; complete scheduler-linked parent/child wait semantics remain unproven | Implement and test exit cleanup, wait queues, child status/reaping, restart policy and service health checks |
| Scheduling/SMP | Architecture context switch, preemption, wakeups and per-CPU execution | Vendored scheduler intentionally does not claim parallel execution; source-level CPU count is not AP startup | Bring up APs, install per-CPU state, switch real task contexts and prove overlapping execution on ≥2 CPUs |
| File descriptors/VFS syscalls | open/read/write/close, fd ownership, file offsets and errno semantics | Native console write is narrow; a complete process-owned VFS/fd path is not proven | Implement fd table and VFS-backed read/write/open/close, user pointer checks, permission tests and /tmp writes |
| PID 1/service manager | Init mounts pseudo filesystems, starts and monitors services, handles failures | Service registry/dependency planning does not by itself launch services | Start actual service executables; require successful start + health checks; test dependency failure and restart |
| Linux userland compatibility | libc/dynamic loader, shell/coreutils, procfs, signals, pipes, sockets, mmap and wait semantics | Compatibility mapping recognizes syscall identities, not full Linux userspace compatibility | Define supported ABI subset; add native libc/sysroot; implement each advertised syscall and test real dynamically/static linked programs |
| Task/process observability | procfs exposes process, memory and CPU state | Scheduler snapshots are internal APIs; TaskMon or shell tools are not proof of procfs-backed telemetry | Expose kernel-owned telemetry and make ps/top/TaskMon read it; no static/mock counts |
| GUI + targets | Init starts display/input/session services; system target is health-checked | Aurora/Marine target definitions and assets exist; desktop readiness requires actual process/display health | Launch the real session from PID 1 and verify display, input, application launch and shutdown |
| Installer/recovery | Target-specific init, persistent storage and meaningful recovery actions | Six-case release verifier and input validator enforce fail-closed checks | Pass each Live/Installer/Recovery × BIOS/UEFI run, installed cold reboot, and recovery postcondition before release |

## Priority implementation plan

- **P0 — Rootfs:** CPIO-newc bounds/path validation; extraction to a real VFS; mount / before process launch; verify /init, /dev, /proc, /tmp.
- **P0 — Process execution:** connect target-specific production ELF to Octavian's native user-entry path; assert real PID and CPL3-originated syscall acknowledgement.
- **P0 — Lifecycle:** implement process-bound exit/wait/reap and descriptor cleanup; never let context-free compatibility dispatch fabricate success.
- **P1 — Userland:** native libc/sysroot, shell, file descriptors, pipes, signals, mmap, procfs and a real service manager.
- **P1 — Targets:** health-checked Aurora/Marine sessions, installer writes and cold reboot persistence, recovery action/postcondition.
- **P2 — SMP:** AP bring-up, per-CPU scheduler entry and real overlapping execution; keep SMP claims blocked until proven.

## Release policy

Do not merge or publish by weakening tests/migration/verify-userspace-handoff.py or manufacturing markers. Required order remains kernel-ready → genuine user-originated syscall acknowledgement → target readiness with the same nonzero PID. Run each of the six target/firmware cases separately against the exact candidate ISO hash. Also require rootfs/VFS, Aurora, installer, recovery and SMP follow-up evidence. Static source checks are necessary but insufficient.

## Linux behavioral references

Use Linux source as a contract reference: init/initramfs.c and fs/ for rootfs/VFS; kernel/fork.c and kernel/exit.c for process lifecycle; arch/x86/entry/ and kernel/sys.c for syscalls; kernel/sched/ for scheduling; fs/proc/ for task telemetry. Adapt semantics to Koronos's own architecture and ABI rather than copying Linux internals.
