# Production userspace handoff — acceptance and integration contract

**Status: BLOCKED.** The latest completed OctavianOS production acceptance remains failed: [native workflow #324](https://github.com/amerhwitat/OctavianOS/actions/runs/39194069056) built Koronos but the unchanged real-userspace verifier failed Live, Installer, and Recovery; prerelease publication was skipped. The current OctavianOS PR #68 head is [`19c0c6d`](https://github.com/amerhwitat/OctavianOS/commit/19c0c6df7d8c173c4f5fe802722814a1451ee45a); native build workflow [#350](https://github.com/amerhwitat/OctavianOS/actions/runs/39196256082) is pending, so the latest mirror changes are not yet verified.

The latest ChimeraIIOS candidate QEMU matrix [#81](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39195918384) completed successfully on commit [`726f07f`](https://github.com/amerhwitat/ChimeraIIOS/commit/726f07f98c83c44be9f73c103004d57d24365a62): Live, Installer, and Recovery passed under both BIOS and UEFI. The diagnosed Live-only `#UD` was caused by compiler-generated SSE2 while CR0/CR4 FP/SSE state was disabled, plus a stack-alignment mismatch for the freestanding C `_start`. The candidate now enables baseline SSE state, initializes x87/MXCSR, uses the correct C entry stack alignment, and returns through an explicit IRETQ frame. This is verified candidate ELF execution only, not production payload acceptance.

The OctavianOS mirror now includes the SSE/stack/IRETQ fixes; a missing recovery initramfs/manifest classification found by its native build test was also fixed. The current mirror adds explicit recovery task registration and logs that production initramfs handoff is withheld when no supported native init/runtime is wired, rather than implying the shell payload was launched. These fail-closed routing changes are under native build validation; they do not themselves execute the real production init.

Production still has the separate init-contract blocker: the ISO passes shell-based initramfs/installer payloads and does not stage a real target-specific `CHIMERA_MODULE_USER_INIT_ELF`. A successful candidate probe cannot be treated as the actual production init. The verifier is unchanged, no readiness markers may be synthesized, and the prerelease gate must remain blocked until the real production payload passes all six BIOS/UEFI × Live/Installer/Recovery cases. Aurora startup, completed installer/reboot, recovery repair, and genuine AP-backed SMP remain independently unverified.

The separate [ChimeraIIOS PR #125](https://github.com/amerhwitat/ChimeraIIOS/pull/125) now has a candidate DPL3 `INT 0x80` gate: the kernel checks the CPU-saved CS RPL and active process CR3 before emitting `USER INIT SYSCALL: target=... init_pid=...`. The probe issues `int $0x80`; the ordinary `SYSCALL` entry is not treated as proof of caller CPL because SYSCALL does not save caller CS. The candidate CI is queued/running on the latest changes and is not yet verified. This remains candidate-only until CI passes and the same execution path is integrated into OctavianOS's production kernel and connected to the actual production init payloads. A probe ELF must not be substituted for the real init.

## What the evidence means

The acceptance job ran the existing verifier unchanged against these traces:

- `trace/full-iso-debugcon.log` for Live
- `trace/installer-debugcon.log` for Installer
- `trace/recovery-debugcon.log` for Recovery

All three failed because they lack both a user-originated init syscall acknowledgement proving CPL 3 and a subsequent target-specific readiness marker carrying the same real, nonzero init PID. The verifier is intentionally fail-closed; do not weaken it or manufacture these markers from kernel code.

## Source-level integration gaps

The current vendored path and the upstream candidate must be treated as separate layers:

1. `process_loader.cpp` validates ELF load segments and maps/initializes memory through callbacks; this alone does not schedule or enter the image.
2. `process.cpp` records ELF metadata/PID admission. Admission is not proof that an instruction executed in ring 3.
3. `interrupt.cpp` installs DPL-0 IDT gates and explicitly defers ring-3 exposure until TSS, stack, and address-space setup are complete.
4. The compatibility `syscall.cpp` dispatcher is not itself a hardware syscall entry/return path; its current GETPID/EXIT semantics are insufficient evidence of process-owned PID and teardown.
5. Multiboot module classification recognizes a possible `CHIMERA_MODULE_USER_INIT_ELF`, but classification is not proof that the ISO build actually stages the target's production init ELF or that the launch path selects it.
6. The current QEMU smoke gates prove kernel readiness and target routing only. They must not be renamed or documented as production userspace acceptance.

Upstream [ChimeraIIOS PR #125](https://github.com/amerhwitat/ChimeraIIOS/pull/125) contains a candidate ring-3 probe path and passed its standalone acceptance workflow. It does **not** by itself prove that the real init executable is extracted from the production Live/Installer/Recovery payload and launched in the final ISO. Do not blindly copy it over OctavianOS-specific source.

**Concrete production-payload mismatch found in source audit:** `tools/build-live-boot-binaries.sh` builds Live and Recovery initramfs images containing a POSIX shell `/init` script and BusyBox applets; `tools/chimera-stage-installer-media.sh` similarly writes a shell `/init` into `installation.img`. The production GRUB entries pass these compressed initramfs/images and metadata modules, not a separate `CHIMERA_MODULE_USER_INIT_ELF`. Therefore, an ELF-only ring-3 launch routine cannot directly execute the current `/init` script, and a standalone probe ELF would not be the actual production init. The design must first provide a real supported userspace contract—such as a native ELF init plus the syscall/runtime facilities needed to start the intended environment, or a deliberately implemented and tested script/interpreter execution path—and stage/route that exact target from each payload. Do not label BusyBox itself as init without validating its ELF ABI, dynamic/static linkage, required syscalls, and intended command behavior.

## Required implementation sequence

1. **Define the production payload contract.** For each target, establish how the actual init executable is identified and extracted from its initramfs/rootfs. Validate archive paths, ELF header/machine/type, PT_LOAD bounds, integer overflow, BSS, entry-point-in-executable-segment, and resource limits. Reject ambiguous/multiple targets.
2. **Stage and route the selected init.** Make the ISO build produce the module or other explicit handoff object consumed by Koronos. Validate the module's identity and target against the selected GRUB/Jasper entry. Do not fall back from Installer or Recovery to Live.
3. **Create an isolated process address space.** Verify process-owned CR3 and page-table lifetime, preserved required kernel mappings, user/supervisor permission bits, non-executable data/stack, W^X, guard pages, and cleanup on every failed load.
4. **Install privilege-transition state.** Verify GDT user descriptors, 64-bit TSS descriptor and `ltr`, valid RSP0 kernel stack, canonical user entry/stack addresses, and a long-mode ring-3 trampoline. Keep interrupts disabled until entry/return invariants are safe.
5. **Implement the real syscall boundary.** Verify MSR setup or an explicitly designed interrupt gate, register/stack ABI, user-origin/CPL validation, safe return state, real per-process GETPID, and EXIT/EXIT_GROUP teardown. Do not use a constant PID or semantic dispatcher as evidence of a hardware syscall.
6. **Emit evidence from the right origin.** The acknowledgement must be emitted only after the syscall entry path proves the caller was at CPL 3. Readiness must be emitted by the running target init after that acknowledgement and carry the same real nonzero PID. Kernel-authored imitation markers are forbidden.
7. **Run the six production cases.** Live, Installer, and Recovery under BIOS and UEFI, with separate trace artifacts and the existing verifier unchanged. Test successful user execution and negative cases (missing module, wrong target, malformed ELF, bad mapping, and init exit before handshake).
8. **Verify the full handoff.** After Live init readiness, prove Aurora/compositor startup. Verify installer completion and booting the installed target, plus a meaningful Recovery action. Test AP startup/per-CPU scheduling separately before making SMP claims.
9. **Gate releases.** The prerelease job must depend on all six production cases and the Aurora/installer/recovery follow-up gates. Any missing trace or verifier failure blocks publication.

## Acceptance matrix

| Production case | Status |
| --- | --- |
| Live / BIOS | NOT VERIFIED — current aggregate Live trace fails |
| Installer / BIOS | NOT VERIFIED — current Installer trace fails |
| Recovery / BIOS | NOT VERIFIED — current Recovery trace fails |
| Live / UEFI | NOT VERIFIED |
| Installer / UEFI | NOT VERIFIED |
| Recovery / UEFI | NOT VERIFIED |
| Aurora after actual Live init | NOT VERIFIED |
| Installer completion + installed boot | NOT VERIFIED |
| Recovery action | NOT VERIFIED |
| Production release | BLOCKED |

The existing aggregate run demonstrates that all three target traces fail; it does not establish six independent BIOS/UEFI outcomes. Record each case separately once the workflow runs them separately.

## Completion evidence

A source change is not complete until CI demonstrates: successful native build; ELF/module contract tests; production payload extraction tests; six target/firmware QEMU runs; verifier PASS for every trace without modifying the verifier; preserved debug traces; and Aurora/installer/recovery follow-up evidence. Until then, report the gate as BLOCKED rather than inferring success from a kernel-ready marker.
