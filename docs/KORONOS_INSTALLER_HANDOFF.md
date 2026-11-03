# Koronos installer userspace handoff status

Date: 2026-11-03

## Current payload

The Jasper Installer menu entry currently boots the Koronos Multiboot2 kernel
with installer metadata/initramfs modules. The installer environment is an
interactive diagnostic shell. It is not a native Koronos installer process,
does not establish a CPL3 process context, and does not perform disk
installation.

The corresponding upstream runtime-integrity correction is tracked in
[ChimeraIIOS PR #237](https://github.com/amerhwitat/ChimeraIIOS/pull/237).
That change removes initramfs-shell `USERSPACE READY` markers and makes the
Koronos installer task report the missing executable init ELF and unimplemented
process-context/CPL3 path explicitly.

## Required native installer handoff

Do not report the OctavianOS installer as userspace-ready until all of these
steps are implemented and independently observed:

1. Supply a real x86-64 installer init ELF and a documented native ABI/sysroot.
2. Validate the Multiboot2 installer module table and the init ELF bounds.
3. Extract the installer initramfs safely and publish a verified VFS root.
4. Map ELF PT_LOAD segments with enforced user/supervisor, writable, NX and W^X
   permissions; map a guarded user stack.
5. Create an owned process address space, process-owned kernel stack, saved
   initial CPU context, and per-process TSS.RSP0 handoff.
6. Switch address spaces safely and enter CPL3 through a validated architecture
   return frame.
7. Dispatch syscalls using trusted per-CPU current-process identity; implement
   real GETPID, EXIT, wait/reap and descriptor/VFS semantics.
8. Require the first user-originated init syscall acknowledgement and a
   subsequent init readiness handshake for the same nonzero kernel-owned PID.
9. Keep disk operations disabled until a separate OS-specific installer backend
   has explicit disk/ESP selection, destructive-operation confirmation,
   bootloader deployment and post-install persistence verification.

## Acceptance and release policy

- A GRUB entry, module list, initramfs shell, scheduler task, or kernel idle-loop
  marker is not proof of a running userspace process.
- The verifier must require ordered kernel-ready -> CPL3-originated init syscall
  -> userspace-ready markers, with the same target and nonzero PID.
- Live, Installer and Recovery require independent target-specific QEMU traces.
- BIOS and UEFI must both be tested. Physical firmware acceptance remains
  separate from hosted QEMU results.
- Keep native-init and installer failures fail-closed. Do not manufacture
  readiness markers or promote diagnostic shell behavior to production status.

This document records the current limitation and acceptance contract; it does
not claim that the native installer loader has been completed.
