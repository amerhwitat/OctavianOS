# Koronos Linux workflow and SMP parity note

Linux is a behavioral reference, not copied code or a claim of Linux ABI compatibility.

## Linux boot/userspace sequence

Linux establishes architecture-specific CPU and memory state, unpacks initramfs into the initial rootfs, executes PID 1, and routes process syscalls through task-aware kernel interfaces. PID 1 supervises services; the distribution supplies libc, dynamic linking, shell/utilities, device management, logging, networking and desktop services.

Koronos must preserve equivalent responsibilities while keeping its own ABI:
1. Validate and unpack a bounded CPIO-newc archive into kernel VFS nodes.
2. Publish the root mount and mount /dev, /proc, /sys and writable /tmp.
3. Create scheduler-owned tasks with address spaces, guarded kernel stacks, saved trap frames and per-process descriptor tables.
4. Enter CPL3; validate/copy every pointer and route OPEN/READ/WRITE/SEEK/CLOSE through the caller's descriptor table.
5. Supervise child processes and services through exit, wait and reap.
6. Prove Live, Installer and Recovery independently on BIOS and UEFI from the same immutable ISO hash.

## Multi-core execution sequence

Linux x86-64 separates firmware topology discovery, AP bring-up and scheduler activation. Koronos' corresponding implementation order is:
1. CPUID leaf 0x1F/0x0B (or AMD extended topology) discovers package logical CPUs, core count, SMT width and the BSP APIC ID. ACPI MADT enumeration of enabled APIC IDs remains required.
2. BSP initialization followed by per-AP startup records, stacks, GDT/TSS and GS/per-CPU anchors.
3. Local APIC INIT/SIPI startup through a low-memory trampoline, with bounded APIC-ID-specific online acknowledgements.
4. Per-CPU run queues and current-task ownership only after AP online; IPIs for rescheduling, TLB shootdown and stop.
5. Saved interrupt frames, address-space switching and TSS.RSP0 handoff integrated into scheduler context switches.
6. Concurrent worker measurements from distinct APIC IDs with overlapping monotonic-clock intervals.

A CPU count, affinity mask, host test, serial stepping helper, or nonzero scheduler return value is not sufficient evidence of parallel execution.

## Current implementation boundary

The bounded PID-keyed descriptor table wraps VFS handles and process reaping closes descriptors. Native SYSCALL and CPL3 INT 0x80 dispatch now route OPEN/READ/WRITE/SEEK/CLOSE through that table. Bounded current-CR3 copy_from_user/copy_to_user helpers validate every covered page before copying. These are kernel-side implementation and host-test foundations; fault-fixup recovery, page pinning, scheduler-owned task identity and real target-init VFS round-trip evidence remain outstanding.

CPUID topology detection now reports package logical processors, physical cores, SMT width and BSP APIC ID. The scheduler deliberately exposes only the BSP as online until AP startup is implemented and acknowledged.

The process table remains an ELF admission/load-plan registry, not a scheduler-owned task lifecycle. ACPI MADT enumeration, AP INIT/SIPI startup, per-CPU interrupt execution, IPIs, scheduler-owned saved contexts and measured overlap remain unimplemented.

Installer disk persistence, Recovery repair postconditions, target-specific production init, and the immutable six-case ISO acceptance also remain blocked. Release stays fail-closed until actual runtime evidence proves every required gate.