# Boot target-to-userspace audit (source review)

**Scope:** source-level inspection of the ChimeraIIOS `main` tree and the existing boot-routing branch on 2026-10-12. This is not a QEMU boot proof.

## Required chain

`Firmware → Spit Fire → Jasper/GRUB menu → Koronos ELF → hardware/driver initialization → scheduler/runtime → selected userspace → Aurora`

The canonical boot-order document is `docs/BOOT_TO_AURORA_SEQUENCE.md`. The progress manifest is `boot/startup/boot_phase_manifest.json`. Preserve the current artwork contract, including the tracked embedded background source; do not reintroduce the obsolete `aurora-background.jpg` scheme.

## Target matrix

| Menu target | Payload handed to Koronos | Expected userspace/GUI | Source-review finding |
|---|---|---|---|
| Live Aurora | `/boot/live/chimera-live-initramfs.img` + live manifest | Live init + Aurora session/compositor | Menu payload contract exists; actual process execution and GUI-ready marker must be proven in QEMU. |
| Normal boot | Main GRUB config in the source tree also passes the live initramfs | Installed system or defined normal target | Current labels and actual payload need to be aligned; do not treat a live payload as an installed-system boot. |
| Installer | Required installer image/manifest/contracts and Aurora installer artwork | Aurora Installer UI and installer service | Original `boot/iso/grub.cfg` installer entry passes the live initramfs. Jasper's `boot/jasper/install.cfg` has a dedicated installer-media contract. The routing PR corrects top-level target routing, but module recognition alone is not execution. |
| Recovery | `/boot/recovery/chimera-recovery-initramfs.img` + recovery manifest | Recovery shell/services and diagnostics | The original main module classifier does not classify recovery module names. The routing PR adds recovery classifications; userspace launch remains unverified. |
| Diagnostics | Diagnostics mode plus recovery payload/manifest | Diagnostics userspace/service | Original config supplies a diagnostics manifest and background but does not prove that recovery userspace starts. The routing PR consumes `chm.mode=diagnostics` and points diagnostics to recovery-backed payloads. |
| Safe graphics | Live or recovery payload with safe-graphics option | Console/recovery without full compositor | Must remain usable if the artwork, GPU, or compositor fails. |
| ARM64/mobile | Architecture-specific kernel and boot media | Mobile/AArch64 userspace | An x86_64 ISO must not launch an x86_64 kernel under an ARM64 label. The routing PR marks unsupported cross-architecture targets unavailable. |

## Koronos handoff observed in source

The inspected `kernel/core/koronos.cpp` path validates the boot context, scans Multiboot2 modules, initializes architecture/CPU discovery, scheduler and learning services, registers drivers, probes hardware/firmware/devices, starts drivers, initializes ELF/process admission in **load-plan mode**, initializes modules, and submits cooperative bootstrap tasks.

The process initialization message explicitly says `load-plan mode`. The existing handoff diagnosis explains why ELF metadata validation and a scheduler task record do not establish an executable userspace process. The inspected function then emits `Entering Koronos scheduler loop`; the call path from that point to a persistent dispatch loop must be verified in the actual linked entry path.

## Installer GUI reality

`installer/gui/aurora-installer.sh` provides a host-userspace script that selects an edition, invokes `chimera_installer.py` to create a reviewed plan, and optionally presents it with Zenity. Its own confirmation text says the current step does not erase disks and that platform-specific disk/boot mutation remains a signed backend operation. This is not yet proof of a freestanding installer ELF being launched by Koronos, nor proof that installation writes a bootable target.

## Required end-to-end acceptance

For every selectable GUI/installer/recovery entry:

1. Resolve the menu ID to its exact configfile chain and final boot commands.
2. Assert every referenced kernel, initramfs, manifest, contract and artwork asset exists in the staged ISO; verify hashes and architecture.
3. Capture Multiboot2 tags and module command lines in the kernel, including mode flags.
4. Verify kernel module classification matches the menu's module names.
5. Verify the selected payload is admitted, loaded, mapped with correct permissions, given a valid stack/ABI/context, and entered through a supported privilege transition.
6. Require an observable userspace ready marker on QEMU debugcon/serial. The marker must be emitted by the target userspace after it starts, not fabricated by the kernel.
7. For Installer, exercise the GUI, storage inventory, review/confirmation, and safe failure paths. Never perform destructive disk operations in CI without an isolated disposable disk image.
8. For Recovery/Diagnostics, prove a recovery shell/service runs when graphics initialization fails.
9. Test missing, corrupt, wrong-architecture and truncated payloads; each must fail closed with a useful diagnostic.
10. Rebuild the final ISO from the tested commit, inspect its contents, record SHA-256, and retain QEMU logs.

## Status

- Static route review: performed.
- OctavianOS installer routing fix: merged as PR #2; top-level Install now enters `/boot/jasper/install.cfg`, whose native path passes the dedicated installation image and contracts rather than the Live initramfs.
- Static regression workflow: passed for the tested commit; this verifies menu-source routing only.
- Source-level installer/recovery execution: **not verified**.
- Actual GUI-ready markers in QEMU: **not verified**.
- Full ISO rebuild on OctavianOS destination: **not run**.
- ISA conformance: separate acceptance track; catalog rows do not imply executable or conformant backends.
