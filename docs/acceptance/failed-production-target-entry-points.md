# Failed production-target entry points

This is a trace-backed implementation map, not a claim that userspace or SMP is working. Keep release publishing blocked until each production acceptance case passes independently.

## Live userspace — blocked

- **Trace-producing entry point:** `vendor/chimera-ii-os/source/kernel/core/koronos.cpp::task_live`.
- **Module discovery:** `chimera_multiboot_find(CHIMERA_MODULE_LIVE_INITRAMFS)`, populated by `vendor/chimera-ii-os/source/kernel/core/multiboot_modules.cpp::chimera_multiboot_scan`.
- **ELF admission:** `vendor/chimera-ii-os/source/kernel/core/process.cpp::chimera_process_admit_elf`, declared in `vendor/chimera-ii-os/source/kernel/include/chimera/process.h`.
- **Failure:** the task logs “Runtime handoff queued” then blocks. ELF admission records a load plan; it does not map segments, build a user stack and ring-3 frame, enter the entry point, or prove a user-originated syscall. Runnable tasks are zero in the captured trace.
- **Next code seam:** replace the log-and-block branch with a selected-target launcher that resolves a verified init ELF from the live initramfs, maps PT_LOAD/BSS into process-owned page tables with user permissions and W^X, builds a user stack, configures kernel entry state, and invokes the architecture-specific ring-3 transition. Readiness requires a syscall acknowledgement from that same PID.

## Installer userspace — blocked

- **Trace-producing entry point:** `vendor/chimera-ii-os/source/kernel/core/koronos.cpp::task_installer`.
- **Inputs:** installation image, manifest, contract, phases and profiles, classified by `chimera_multiboot_scan`.
- **Failure:** the phase switch logs metadata progress only; phase 3 states graphical installer userspace is not running and phase 4 blocks awaiting a loader that is not connected.
- **Next code seam:** after validating metadata, launch the verified installer init ELF through the shared process-launch primitive. Gate readiness on real ring-3 entry and syscall evidence. Keep storage mutation disabled until disk discovery, partitioning, filesystem mounting and durable write/readback tests pass.

## Recovery userspace — blocked

- **Trace-producing entry point:** `vendor/chimera-ii-os/source/kernel/core/koronos.cpp::task_recovery`.
- **Input:** `CHIMERA_MODULE_RECOVERY_INITRAMFS`.
- **Failure:** module acceptance is followed by “repair shell has not been entered”; the task then blocks.
- **Next code seam:** resolve a recovery init ELF and shell from the archive, launch via the shared process-launch primitive, then test read-only diagnosis and an explicitly scoped repair/write with post-write verification.

## Shared blockers

1. `chimera_process_admit_elf` is validation/admission, not execution. Implement frame allocation, PT_LOAD/BSS mapping, permissions, stack mapping, and architecture transition; reject non-user ranges and W+X.
2. Bind syscall entry to authoritative active process identity and address space. Caller-supplied PID/UID/GID is not authority.
3. Implement validated user-copy for paths, strings and buffers; never hand raw ring-3 pointers to VFS.
4. Put file descriptors in process state, close on exit, and enforce fd ownership/permissions. Add native OPEN/CLOSE/SEEK dispatch only after trusted context and pointer validation exist.
5. Mount validated CPIO initramfs read-only, reject malformed archives/path traversal, and resolve target-specific executable paths.
6. Connect EXIT/EXIT_GROUP to scheduler exit, descriptor cleanup and wait/reap; fail-closed compatibility dispatch is not lifecycle support.
7. Genuine SMP requires AP startup, per-CPU stacks/interrupt state and concurrent dispatch. Serial scheduler stepping is not SMP; current boot trace explicitly reports AP startup unimplemented.

## Acceptance matrix

Run Live, Installer and Recovery independently under BIOS and UEFI (six separate cases). Record firmware, target payload hash, PID, ring-3 entry, user-originated syscall acknowledgement, exit/wait, relevant filesystem evidence, and raw trace. Unrun cases are NOT RUN. SMP passes only with AP startup and concurrent execution on distinct CPU IDs.

## Source entry points to update first

- `vendor/chimera-ii-os/source/kernel/core/koronos.cpp::task_live`
- `vendor/chimera-ii-os/source/kernel/core/koronos.cpp::task_installer`
- `vendor/chimera-ii-os/source/kernel/core/koronos.cpp::task_recovery`
- `vendor/chimera-ii-os/source/kernel/core/koronos.cpp::koronos_boot`
- `vendor/chimera-ii-os/source/kernel/core/process.cpp::chimera_process_admit_elf`
- `vendor/chimera-ii-os/source/kernel/core/syscall.cpp::chimera_syscall_dispatch`
- `vendor/chimera-ii-os/source/kernel/core/vfs_fd.cpp` and `vfs.cpp`
- `vendor/chimera-ii-os/source/kernel/core/cpio.cpp::chimera_cpio_find`
