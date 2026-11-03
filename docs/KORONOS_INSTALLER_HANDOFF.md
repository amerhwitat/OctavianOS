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


## Existing Init.mp4 boot indicator

The Octavian live-image build consumes the existing
`vendor/chimera-ii-os/source/desktop/aurora/assets/Init.mp4` asset (the
`assets/library/Init.mp4` copy must remain byte-identical). It stages the same
video at `/boot/visual/Init.mp4`, `/boot/spitfire/Init.mp4`,
`/boot/jasper/Init.mp4`, and `/boot/grub/Init.mp4`, and retains the runtime
copy at `/usr/share/chimera/aurora/assets/Init.mp4`. A SHA-256 manifest records
the source bytes and stage paths.

GRUB/Jasper do not decode MP4. Their SVG/JPEG/framebuffer artwork and verbose
text progress remain the early boot indicator; the GRUB menu only reports that
the media is present. The Linux/Openbox Aurora live session invokes the existing
Aurora splash player after Openbox becomes ready and before starting the
fullscreen kiosk. Playback is bounded to 12 seconds and is not a prerequisite
for desktop startup. This is a Linux live-session visual, not evidence of
native Koronos userspace readiness or a native Installer/Recovery handoff.
