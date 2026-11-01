# OctavianOS boot sequence and target routing trace

**Scope:** source-level audit of the OctavianOS destination tree. This document does not claim an ISO was rebuilt or that a menu entry reached a running userspace in QEMU.

## Canonical boot chain

`Firmware → Spit Fire (if selected) → GRUB 2 / Jasper target menu → Koronos ELF → hardware and driver initialization → scheduler/runtime → selected userspace payload → desktop/session readiness`

GRUB `configfile` switches menu configuration; it does not start an application by itself. The Multiboot2 commands pass the kernel and named modules. The kernel must recognize those module names and command-line options, admit and execute the userspace payload, and then the userspace must start the selected session. GNU GRUB documents menu entries and configuration loading as separate menu/script operations ([GRUB manual](https://www.gnu.org/software/grub/manual/grub/grub.html)).

## Menu/configuration graph

- `boot/iso/grub.cfg` is the top-level GRUB menu.
- `--id normal` opens `boot/jasper/jasper.cfg`; it is a target selector, **not** a claim that an installed system was found.
- `--id aurora-live` passes `chm.mode=live chm.desktop=aurora`, then the live initramfs, live manifest, and optional desktop-session selection manifest.
- `--id marine-live` passes `chm.mode=live chm.desktop=marine` with the same Live payload contract.
- `--id install` checks the installation image, manifest, contract, phases and profiles before opening `boot/jasper/install.cfg`.
- `--id recovery` opens `boot/jasper/recovery.cfg`; `--id diagnostics` opens `boot/jasper/diagnostics.cfg`.
- `--id safe-mode` opens `boot/jasper/safe.cfg`, which requests `chm.mode=safe chm.graphics=basic`.
- `--id retro` opens `boot/jasper/retro.cfg`; it fails closed when the optional retro initramfs/manifest is absent.
- `--id spitfire` opens `boot/spitfire/spitfire-menu.cfg`, which can route back to Jasper, Live, Installer, Recovery or Diagnostics.
- UEFI-only entries open Jasper, the installation alias, recovery, diagnostics, retro and Spit Fire menus; firmware setup is shown only where GRUB supports it.
- Mobile/ARM64 is explicitly unavailable in this x86_64 ISO rather than mislabeling an x86_64 kernel as ARM64.
- Last Known Good requires a staged rollback initramfs and manifest. If absent, the menu reports that no rollback snapshot is available instead of silently booting the Live image.

## Target contract matrix

| Target | Final kernel/payload contract | Expected userspace target | Source-level status |
|---|---|---|---|
| Live Aurora | Koronos ELF + live initramfs + live manifest + desktop selection contract | **Aurora Wayland Glass Desktop** | Menu passes a desktop selection request; live userspace parsing and GUI readiness are unverified |
| Live Marine | Same Live payload, `chm.desktop=marine` | **Marine Desktop** | Separate menu path and manifest entry exist; native session launch is unverified |
| Native Installer | Koronos ELF + installation image + installation manifest + contract + phases + profiles | Installer userspace / Aurora Installer UI | Required-file guards and Multiboot modules are present; installer process execution and safe disk backend are unverified |
| Legacy installer alias | Installer initrd + manifest/contract + hardware/compatibility/N-bit policy files | Compatibility installer path | Fails closed if any required module is missing; runtime support unverified |
| Recovery | Koronos ELF + recovery initramfs + recovery manifest | Recovery shell and recovery services | Config/guards present; module classifier and shell startup need runtime proof |
| Diagnostics | Recovery payload plus `chm.mode=diagnostics` | Diagnostics console/services | Mode request is passed; kernel/userspace consumption unverified |
| Safe graphics | Live payload plus `chm.mode=safe chm.graphics=basic` | Text/basic-graphics fallback | Config path present; actual GPU/compositor bypass unverified |
| Services | Live payload plus `chm.mode=services` | Service profile | Request is passed; service manager behavior unverified |
| Retro / Emulator Center | Optional retro initramfs + manifest | Retro/emulator userspace | Explicitly unavailable unless those payloads are staged |
| Mobile / ARM64 | Architecture-specific kernel and boot chain required | Mobile session | Unavailable in current x86_64 ISO |
| Last Known Good | Rollback initramfs + rollback manifest required | Previous known-good deployment | Explicitly unavailable when rollback artifacts are absent |

## Required build outputs versus tracked sources

The repository tracks boot configuration and the desktop-selection contract. The following are **generated or imported ISO payloads**, not currently proven present just because a GRUB config references them:

- `/boot/koronos/koronos.elf`
- `/boot/live/chimera-live-initramfs.img` and `/boot/live/live-manifest.json`
- `/boot/recovery/chimera-recovery-initramfs.img` and `/boot/recovery/recovery-manifest.json`
- `/install/installer/installation.img`, manifest, contract, phases and profiles
- Optional retro and rollback payloads
- Aurora/Marine session executables and their session manifests

The source-level payload contract is tracked in `boot/iso/target-payload-contract.json`. The ISO staging/build pipeline should run `python3 tools/boot/validate_iso_payloads.py --root <extracted-or-staged-iso-root>` before packaging. The validator checks required files, ELF64/x86_64 identity, the Multiboot2 header/checksum, JSON payloads, and complete-or-absent optional bundles; an optional SHA-256 manifest can pin expected payload hashes. This is a packaging gate, not a boot test. Missing payloads should fail the build or show the menu's explicit failure message. Do not use the live initramfs as a substitute installer or claim that a desktop selection request proves a desktop is running.

## Koronos/userspace handoff gates

The previous source audit found process admission in `load-plan mode`. That state is not proof of ELF userspace execution. To close the handoff, runtime work must:

1. Capture Multiboot2 tags and module command lines on serial/debugcon.
2. Verify the kernel recognizes all module ABI names used by these configs.
3. Parse the `chm.mode`, `chm.graphics`, `chm.desktop` arguments in a defined and tested boot-options parser.
4. Validate payload format, architecture, bounds, manifest and hashes before admission.
5. Map code/data/stack with appropriate permissions, establish the process ABI and privilege transition, and execute the entry point.
6. Emit readiness markers from the target userspace after it starts. A GRUB echo or kernel banner is not a GUI-ready marker.
7. For Aurora and Marine, verify the selected session manager launches the requested desktop and emits a session-ready marker; if startup fails, enter safe text recovery.
8. For Installer, verify UI, storage inventory, reviewed plan, explicit confirmation, and non-destructive failure paths using only disposable CI disk images.
9. For Recovery/Diagnostics, prove a shell/service starts without GPU/compositor dependencies.
10. Build the ISO from the tested commit, inspect ISO contents, record SHA-256, and retain QEMU logs/screenshots.

## Validation status

- Configfile graph and target IDs: covered by `tests/boot/test_boot_target_graph.py` (static test).
- Installer module routing: covered by `tests/boot/test_installer_payload_routing.py` (static test).
- GRUB parser check: workflow runs `grub-script-check` on tracked GRUB configs.
- ISO rebuild and asset-presence verification: not yet run in this destination repository.
- QEMU/physical boot, executable userspace handoff, Aurora/Marine readiness, installer disk workflow: not verified.
