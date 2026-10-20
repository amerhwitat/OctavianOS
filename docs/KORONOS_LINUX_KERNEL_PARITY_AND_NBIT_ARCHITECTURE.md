# Koronos/Linux kernel parity and N-bit execution boundary

**Status: NOT IMPLEMENTED as a complete Linux compatibility layer.** This is the OctavianOS integration plan aligned with [ChimeraIIOS PR #174](https://github.com/amerhwitat/ChimeraIIOS/pull/174). It must not be interpreted as a claim that Linux binaries, services, drivers, or desktop environments already run.

## Current evidence and gaps

| Layer | Existing Koronos evidence | Required production implementation |
|---|---|---|
| ELF / address space | ELF validation and loader callbacks; process metadata admission | Process-owned page tables wired to scheduler and ring-3 entry, page faults, copyin/copyout, BSS/stack/TLS/auxv, teardown |
| Syscall ABI | OS/entry recognizer and limited Linux syscall-number translation | Per-process ABI personality, exact x86-64/i386 register contracts, user-pointer validation, Linux errno mapping, implemented backends |
| Process lifecycle | Process metadata table and scheduler primitives | Real current-task identity, PID ownership, exit/exit_group teardown, spawn/wait/reap, signals and thread groups |
| VFS | Initramfs modules and archive parsing/handoff work | Validated root VFS, path lookup, stat/open/read/close, process-owned FD tables, filesystem/storage backends |
| Scheduler | Kernel scheduler/task/thread components | Proven context switching, block/wake/timer semantics, wait queues, per-CPU run queues and AP-backed SMP |
| Devices | Generic PCI/virtio/display driver objects | Real probe/bind/resource/DMA/interrupt lifecycle and device-facing APIs |
| Services | Kore service manifest/orchestration metadata | Actual service processes, dependency order, health checks, logs, restart policy and failure propagation |
| Linux userland | No complete Linux application acceptance trace | Start with static single-threaded x86-64 CLI programs, then dynamic loader, TLS, futexes, signals, poll/epoll, sockets and broader POSIX |
| Desktop / destinations | Aurora assets and ISO candidate builds | Working framebuffer/input/compositor/session, installer disk write and installed boot, real recovery operation |

## Linux syscall mapping safety

The existing syscall translation table had aliases for unsupported calls that could map to unrelated canonical operations (notably `open`/`close` and `mprotect`). ChimeraIIOS PR #174 changes these mappings so unsupported calls remain unrecognized and fail closed, and adds a host-side regression test to the Koronos build. This protects ABI correctness but does not implement the corresponding system calls. The PR must pass CI before the change is accepted.

The syscall entry mechanism alone must not determine process personality. Linux, Chimera-native, and other ABI contexts need explicit per-process identity. A translated syscall number is not proof that a backend exists; until the backend and pointer validation are implemented, the result must remain ENOSYS.

## Linux-kernel-style architecture for Koronos

Keep kernel-space components minimal and privileged:
- architecture entry, firmware/HAL, interrupts and timers
- physical/virtual memory, address spaces and page faults
- scheduler, synchronization, process/thread lifecycle
- syscall dispatch and ABI adapters
- VFS core, filesystem drivers and descriptor primitives
- bus/device/driver model, DMA/resource control
- IPC/capability and security primitives

Run policy and complex services in isolated userspace processes:
- PID 1 init/supervisor and dependency manager
- device manager, storage/mount manager, logging/event service
- network configuration and network services
- authentication/policy service
- terminal/session manager, input/audio and Aurora compositor
- package/update manager, installer orchestration and recovery tools

A service registry is not a running service. Only a real process with a successful health check can be reported healthy.

## N-bit virtual CPU separation

Keep three concepts separate: (1) physical native ISA (currently x86-64 for the ISO), (2) application ABI/pointer width (Linux x86-64 or i386, for example), and (3) guest virtual CPU profile (8 through 8192 bits). Wider-than-hardware profiles require a real interpreter/JIT/emulator defining registers, flags, instruction semantics, exceptions, memory ordering, privilege, devices and serialization. Alternate ELF note sections or build variants are metadata only, not evidence of an operational virtual CPU. Linux x86-64 applications still need an x86-64-compatible execution engine and Linux syscall personality.

## Acceptance sequence

1. Correct syscall translation and run ABI regression tests.
2. Bind personality and syscall entry to the current process; implement genuine GETPID and exit/reap semantics.
3. Implement user memory validation and process-owned address spaces.
4. Implement bounded CPIO-backed read-only VFS and per-process file descriptors.
5. Prove a static Linux x86-64 test program can open/read a known file and exit with status zero.
6. Add wait queues, timers, thread groups, futexes, signals, pipes, poll/epoll and sockets.
7. Start PID 1 and target services as real processes with dependency and health checks.
8. Prove Live/Aurora, Installer → disk → reboot → installed OS, and Recovery action for BIOS and UEFI.
9. Prove AP startup and concurrent per-CPU execution independently.

**Release gate remains BLOCKED** until runtime evidence passes the unchanged six-case production verifier and destination-specific tests.
