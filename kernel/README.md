# Kernel source and release gate

## Current integration topology

The canonical Koronos implementation is currently built from the pinned
Chimera source snapshot at
`vendor/chimera-ii-os/source/kernel/` by
`.github/workflows/native-koronos-build.yml`. This is a vendored-source build,
not an independent implementation under OctavianOS's top-level `kernel/`
directory. Do not describe the vendored snapshot as a destination-native kernel
port, and do not publish a release ISO by substituting documentation, a mock
binary, or the host kernel.

The vendor snapshot includes the freestanding x86_64 kernel, boot entry,
ELF loader, scheduler, Multiboot2 module classification, and source-level
handoff verifier. It does not yet prove that OctavianOS has a real init process
running in ring 3, nor that the GTK shell runs directly on Koronos.

## Required kernel deliverables

- `kernel/koronos/`: destination-owned boot entry, architecture setup, exceptions/interrupts, scheduler and process runtime, or an explicit, tested vendored-source integration contract.
- `kernel/arch/x86_64/`: x86_64 boot handoff and hardware setup.
- `kernel/arch/aarch64/`: independent ARM64 boot handoff for mobile-capable builds.
- `kernel/microkernel/`: IPC, address-space/process isolation, capability policy and service supervision.
- `kernel/abi/`: versioned boot information, `chm.mode` / `chm.desktop` parsing, module handoff and userspace ELF admission.
- `kernel/tests/`: host tests plus QEMU serial/readiness acceptance tests.

## Release acceptance

The release workflow must fail closed unless a real kernel ELF and the
required target-specific userspace payloads pass ISO contract checks. A passing
C unit test is not a boot test; a booted kernel is not a ready desktop. The
userspace handoff gate requires an ordered kernel-ready marker, a first
user-originated syscall acknowledgement (proving execution reached CPL 3), and
a target-specific readiness marker carrying the same real nonzero PID.

Run separate QEMU acceptance cases for Live, Installer, and Recovery. Installer
acceptance must prove installation completed and the installed system booted;
Recovery must prove a repair action completed, not merely that recovery init
started. Keep genuine SMP and direct Koronos GUI acceptance separate from
userspace-init readiness.

## Migration source and provenance

Upstream: https://github.com/amerhwitat/ChimeraIIOS

Use the dedicated `OCTAVIANOS_IMPORT_TOKEN` Actions secret only for the history
importer. Do not place credentials in source or logs. Port code with provenance
and license metadata; do not flatten all source repositories into one tree.


## Architecture execution status — explicitly NOT VERIFIED (2026-10-18)

The source-integration workflow passed, but it validates the vendored-source integration and host-side gates, not real ring-3 execution: https://github.com/amerhwitat/OctavianOS/actions/runs/39126424369

Open implementation blockers inherited from the current Koronos source include hardware page-table enforcement for user/supervisor, RW, NX and W^X; process-owned address spaces and saved CPU contexts; user GDT selectors and TSS/RSP0; a validated CPL-3 syscall entry/return path; kernel-owned PID lookup and real exit/cleanup semantics; and architecture-level process scheduling. A passing verifier test cannot substitute for any of these.

Do not mark the destination kernel as a native OctavianOS port merely because CI builds the vendored Chimera snapshot. Do not publish a release ISO until independent QEMU Live, Installer and Recovery runs demonstrate real init execution and target-specific behavior. Keep SMP and direct Koronos GUI claims separately gated.
