# Linux v7.2.2 boot-handoff audit for Koronos

Status: **design/reference audit plus a narrow CPIO hardening change; not production handoff acceptance**.

## Upstream source areas reviewed

The requested Elixir Bootlin tag is the reference baseline. The web reader could not render the Elixir pages directly in this run, so treat these links as the exact upstream paths to inspect in a full source checkout, not as a claim that every line has been exhaustively audited:

- `init/main.c`: https://elixir.bootlin.com/linux/v7.2.2/source/init/main.c
- `init/initramfs.c`: https://elixir.bootlin.com/linux/v7.2.2/source/init/initramfs.c
- `init/do_mounts_initrd.c`: https://elixir.bootlin.com/linux/v7.2.2/source/init/do_mounts_initrd.c
- `fs/exec.c`: https://elixir.bootlin.com/linux/v7.2.2/source/fs/exec.c
- `fs/binfmt_elf.c`: https://elixir.bootlin.com/linux/v7.2.2/source/fs/binfmt_elf.c
- `kernel/fork.c`: https://elixir.bootlin.com/linux/v7.2.2/source/kernel/fork.c
- `kernel/exit.c`: https://elixir.bootlin.com/linux/v7.2.2/source/kernel/exit.c
- `arch/x86/kernel/head_64.S`: https://elixir.bootlin.com/linux/v7.2.2/source/arch/x86/kernel/head_64.S
- `arch/x86/entry/entry_64.S`: https://elixir.bootlin.com/linux/v7.2.2/source/arch/x86/entry/entry_64.S
- `arch/x86/kernel/process.c`: https://elixir.bootlin.com/linux/v7.2.2/source/arch/x86/kernel/process.c
- `lib/decompress_inflate.c` and `lib/inflate.c`: https://elixir.bootlin.com/linux/v7.2.2/source/lib/decompress_inflate.c and https://elixir.bootlin.com/linux/v7.2.2/source/lib/inflate.c

Supplementary source view available in this run: Linux upstream `init/initramfs.c` and `init/main.c` pages on GitHub. The architectural lesson is the staged boundary: architecture entry and early initialization, scheduler/task creation, initramfs extraction, executable-format validation/loading, then a real PID 1 handoff. These layers are distinct; a boot banner or successful ELF probe is not a userspace service.

## Mapping to Koronos

1. **Boot entry and architecture setup** — audit Multiboot2/GRUB entry assumptions, CPU mode, GDT/TSS, interrupt state, physical memory map and reserved ranges before invoking C++ runtime services.
2. **Bounded initramfs extraction** — parse archive-relative offsets with checked arithmetic; validate CPIO header fields, file type, checksums and mandatory trailer. Compressed input must go through a separately tested bounded gzip/DEFLATE implementation; do not feed gzip bytes to the CPIO parser.
3. **ELF loading** — validate the full ELF header and program-header table, target machine/type, PT_LOAD file/memory bounds, page-rounded overlaps, canonical user ranges, W^X/NX, executable entry point, and non-overlapping stack. Roll back all mappings on any partial failure.
4. **Process and address-space ownership** — bind the admitted PID to the scheduler task and its owned CR3/address-space object. Do not treat a load plan as a running process; don't use a global or hard-coded PID as current-task identity.
5. **Ring-3 entry and syscall return** — verify user entry ABI/stack alignment, privilege transition, TSS RSP0, saved register frame, user-buffer validation, and error/exit paths. A CPL3-origin marker must be derived from the saved privilege frame, not from a claimed RIP alone.
6. **PID 1 readiness** — only the selected production init may issue a target-specific readiness handshake, after successful userspace syscalls, with the same nonzero scheduler-owned PID. The kernel must not synthesize the readiness marker.
7. **Target behavior** — Live must launch a real session/compositor and report session readiness; Installer must perform safe storage/install/verification/reboot operations; Recovery must perform concrete diagnostics/repair operations. A shell script or smoke probe is not a native production service.
8. **Timeouts and teardown** — use a verified timer/interrupt path, bounded phases, deterministic failure markers, task exit/reap semantics and address-space reclamation. A timeout must not depend on a process making a syscall.
9. **SMP** — keep serial scheduler stepping labelled as simulation until AP startup, per-CPU current-task ownership, locks/atomics, and genuinely concurrent QEMU SMP tests pass.

## Code change in this branch

`vendor/chimera-ii-os/source/kernel/core/initramfs.cpp` now parses CPIO `c_mode` and `c_nlink` for validation, rejects zero link counts, requires the `TRAILER!!!` record to have the expected NUL-terminated name and zero data size, and only accepts a regular-file inode as the candidate ELF. This is intentionally a narrow fail-closed hardening change. It does **not** add gzip support or implement the full Linux-like handoff.

## Mandatory next steps / evidence gate

- Implement or port a small freestanding inflater only after auditing the exact Linux v7.2.2 decompressor/inflater code and its license/dependencies. Enforce input/output/work limits and gzip flags, CRC32 and ISIZE; test truncated, malformed, concatenated, and oversized streams.
- Add regression tests for every parser rejection branch and run them through the canonical `build-koronos.sh` and ISO build.
- Stage actual independent native ELF64 Live/Installer/Recovery init payloads, not `user_init_smoke.c` probes.
- Verify the full process-owned syscall/VFS/console/input/timer/wait/mapping lifecycle and target-specific operations.
- Run six separate production boots (Live/Installer/Recovery × BIOS/UEFI), preserving raw serial/debug traces and verifier output. Also verify Live→Aurora, installer install/reboot/installed boot, recovery operations, and AP-backed concurrent SMP.
- Keep release publication blocked until all required checks pass. Report unrun cells as NOT RUN and never infer PASS from routing or synthetic ring-3 probes.

## Licensing and porting note

Use upstream Linux as an architectural and implementation reference, preserve applicable notices if code is copied, and audit GPL-2.0 obligations before copying Linux implementation code into a repository with a different licensing policy. Do not copy kernel code wholesale or assume Linux's MM, VFS, task, allocator, or decompressor APIs exist in Koronos.
