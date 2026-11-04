# Koronos Linux workflow and SMP parity note

This note mirrors the engineering boundary documented in ChimeraIIOS. Linux is a behavioral reference, not a source of copied code or a claim of Linux ABI compatibility.

## Linux boot/userspace sequence

Linux establishes architecture-specific CPU and memory state, unpacks initramfs into the initial rootfs, executes PID 1, and routes process syscalls through task-aware kernel interfaces. PID 1 supervises services; the distribution supplies libc, dynamic linking, shell/utilities, device management, logging, networking and desktop services.

Koronos must preserve equivalent responsibilities while keeping its own ABI and fail-closed gates:
1. Validate and unpack a bounded CPIO-newc archive into kernel VFS nodes.
2. Publish the root mount and mount /dev, /proc, /sys and writable /tmp.
3. Create a scheduler-owned task with an address space, guarded kernel stack, saved trap frame and per-process descriptor table.
4. Enter CPL3; validate every pointer and route OPEN/READ/WRITE/SEEK/CLOSE through that task's descriptor table.
5. Supervise child processes and services through exit, wait and reap.
6. Prove Live, Installer and Recovery independently on BIOS and UEFI from the same immutable ISO hash.

## Multi-core execution sequence

Linux x86-64 separates firmware topology discovery, AP bring-up and scheduler activation. Koronos' corresponding implementation order is:
1. CPUID feature/APIC discovery and ACPI MADT parsing; identify enabled processor/APIC IDs.
2. BSP initialization followed by per-AP startup records, stacks, GDT/TSS and GS/per-CPU anchors.
3. Local APIC INIT/SIPI startup through a low-memory trampoline, with bounded APIC-ID-specific online acknowledgements.
4. Per-CPU run queues and current-task ownership only after AP online; IPIs for rescheduling, TLB shootdown and stop.
5. Saved interrupt frames, address-space switching and TSS.RSP0 handoff integrated into scheduler context switches.
6. Concurrent worker measurements from distinct APIC IDs with overlapping monotonic-clock intervals.

A CPU count, affinity mask, host test, serial stepping helper, or nonzero scheduler return value is not sufficient evidence of parallel execution.

## Current implementation boundary

The bounded PID-keyed descriptor table wraps kernel VFS handles and closes descriptors when a process record is reaped. Its API accepts kernel buffers only; it is not yet wired to CPL3 syscalls and does not supply user-copy validation. The process table remains an ELF admission/load-plan registry, not a scheduler-owned task lifecycle.

The scheduler has logical CPU slots and affinity metadata, but parallel dispatch intentionally returns zero. ACPI/AP startup, per-CPU interrupt execution, IPIs, scheduler-owned saved contexts and measured overlap remain unimplemented. Installer disk persistence, Recovery repair postconditions and the immutable six-case ISO acceptance also remain blocked.

Release stays fail-closed until actual runtime evidence proves every required gate.