# OctavianOS / ChimeraIIOS parity against Linux kernel 7.x

**Status:** engineering comparison only. This document does not claim Linux ABI parity, a native OctavianOS kernel port, or Koronos userspace readiness.

## Canonical source topology

OctavianOS currently builds Koronos from the pinned ChimeraIIOS source snapshot under
`vendor/chimera-ii-os/source/`. The top-level `kernel/` directory is an integration
contract and documentation area, not a separate, complete native kernel implementation.

The vendor metadata is now internally consistent: both
`vendor/chimera-ii-os/SNAPSHOT-MANIFEST.json` and
`vendor/chimera-ii-os/UPSTREAM_REVISION` pin
`474208f9d05af9d16707b5878b63fd78e0d8e911`. This is a historical source pin, not the
current ChimeraIIOS main head.

The new upstream ChimeraIIOS transactional initramfs VFS work is being reviewed in
[ChimeraIIOS PR #241](https://github.com/amerhwitat/ChimeraIIOS/pull/241). It is not yet
merged into the canonical source snapshot; the Octavian vendor snapshot must be refreshed
only after the upstream change is merged and its native build/boot gates pass. Do not copy a partially reviewed kernel
snapshot into OctavianOS or report it as integrated.

## Linux 7.x behavioral baseline

Linux 7.x's early boot flow expands the compressed CPIO initramfs into rootfs, then
executes `/init` as PID 1. PID 1 mounts required pseudo-filesystems, discovers or
switches to the real root when appropriate, and starts the rest of userspace. The Linux
VFS is a filesystem-object and operation layer with path lookup, mount handling and
file operations; it is not simply a table of archive entries. The service manager is
userspace running as PID 1, not code inside the Linux kernel.

References:
- [Linux 7.2 rootfs and initramfs](https://docs.kernel.org/7.2/filesystems/ramfs-rootfs-initramfs.html)
- [Linux VFS/filesystem documentation](https://www.kernel.org/doc/html/latest/filesystems/)
- [Linux 7.2 filesystem documentation index](https://docs.kernel.org/7.2/filesystems/index.html)

## Current parity matrix

| Capability | Linux 7.x contract | Current Chimera / Octavian evidence | Remaining work |
|---|---|---|---|
| Initramfs | Decompress CPIO archive into rootfs and execute /init | CPIO newc walker validates raw 070701/070702; PR #241 adds transactional root publication for raw archives | Merge and test VFS work; support the actual compressed ISO format; prove target module identity and /init execution |
| VFS | Superblock/inode/dentry/file objects, pathname lookup, mount points and filesystem operations | PR #241 adds a bounded archive-backed node tree and atomic root pointer | Full path walk, file ops, mounts, permissions, mutation, reference lifetimes and error semantics |
| Pseudo-filesystems | /dev, /proc, /sys, /tmp and device-backed nodes | No complete kernel-backed pseudo-filesystem set demonstrated | Implement device nodes, procfs, sysfs and bounded writable tmpfs; test actual mounts |
| Process entry | execve establishes address space, stack/auxv and enters user mode | ELF load-plan/admission exists; CPL3 entry/return remains incomplete | Address-space activation, TSS/RSP0, saved contexts, validated ring-3 transition |
| Syscalls and FDs | Calling task identity, validated user pointers, process-owned descriptors and POSIX semantics | Native dispatch and process-owned fd table not complete | Trusted current-process lookup; open/read/write/seek/close; fd lifetime; exec/exit/wait/reap |
| Scheduler/SMP | Per-CPU runqueues, context switching, AP startup and preemption | Cooperative scheduler; one online CPU; parallel dispatch intentionally unavailable | AP bring-up, per-CPU scheduling, timer preemption and SMP stress tests |
| PID 1/services | Userspace init starts dependency-ordered services and tracks failures | Kore service registry/ordering is present but does not yet launch and health-check real processes | Real PID 1, service execution, restart policy, logging, health checks and target completion |
| Desktop | Kernel exposes input/display/process primitives; compositor and shell are userspace | Aurora/Marine GTK and WebKit previews run in host Linux live editions | Direct Koronos graphics/input services, compositor/session manager, VFS-backed file manager and process-backed app launch |
| Release acceptance | Boot tests prove the real image and runtime contract | Linux live ISO tests do not prove native Koronos execution | Same immutable ISO SHA across Live/Installer/Recovery × BIOS/UEFI, same real PID, installer persistence, recovery postcondition and SMP overlap |

## Release boundary

The current Octavian live image is a Linux-kernel live edition. Its GTK/WebKit desktop,
menus, shortcuts and VoiceConnect launch entries are host-user-space integrations. They
must not be presented as a direct Koronos desktop or as proof that native services run.

The native-init exit-78 gate remains intact. Never manufacture kernel-ready, CPL3 syscall,
userspace-ready, installer-complete or recovery-success markers. Keep source builds,
host contract tests, QEMU boot evidence and physical-device acceptance as separate gates.
