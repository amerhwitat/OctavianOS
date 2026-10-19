# OctavianOS

OctavianOS is the successor identity for the ChimeraIIOS operating-system research project. This repository is the destination for the source/history migration, build pipeline, boot/runtime work, ISA catalog, and Aurora desktop.

## Migration status

A GitHub Actions importer is being staged to preserve the source repository's branches and tags under `chimera-import/*` refs. This keeps the original project untouched and avoids overwriting the destination bootstrap branch. Imported source history is not the same as a completed rename; the OctavianOS working tree and builds must still be migrated and validated. The source-history workflow currently requires the repository secret `OCTAVIANOS_IMPORT_TOKEN` with contents and workflows write access.

- Source repository: https://github.com/amerhwitat/ChimeraIIOS
- Required boot path: **Spit Fire → Jasper/GRUB → Koronos ELF → hardware/driver initialization → scheduler/runtime loop → live/recovery/installer userspace → Aurora**
- Build outputs must be rebuilt and tested; renaming an artifact is not validation.
- Installer and recovery acceptance requires observable userspace execution in QEMU, not just payload classification.
- ISA status must distinguish documented, cataloged, encoded/decoded, executed, and conformance-tested.

## Production userspace acceptance — currently blocked

The latest completed full-ISO production Live/Installer/Recovery QEMU run (workflow `39187330633`) fails the fail-closed userspace handoff verifier. The current syscall honesty correction is under review in [ChimeraIIOS PR #147](https://github.com/amerhwitat/ChimeraIIOS/pull/147) and mirrored here in [OctavianOS PR #68](https://github.com/amerhwitat/OctavianOS/pull/68); their CI runs are pending/in progress and neither PR proves ring-3 execution. Kernel readiness and target-routing smoke tests are not proof that init executed at CPL 3. The production ISO must not be released until the real payload is selected and launched, the syscall acknowledgement and readiness markers match the same real PID, all six BIOS/UEFI × target cases pass, and the follow-on Aurora/installer/recovery gates are verified.

- [Production userspace handoff and acceptance contract](docs/PRODUCTION_USERSPACE_HANDOFF.md)
- [Latest failing acceptance run](https://github.com/amerhwitat/OctavianOS/actions/runs/39187330633)
- [Tracking issue #47](https://github.com/amerhwitat/OctavianOS/issues/47)

This documentation records the verified failure state; it does not claim the kernel execution path is fixed.

## Runnable Chimera hosted runtime

The vendored Chimera II hosted user-mode bridge is exposed through an OctavianOS entry point:

```sh
python3 tools/chimera/chimera-hosted info
python3 tools/chimera/chimera-hosted compat list
python3 tools/chimera/chimera-hosted isa
python3 tools/chimera/chimera-hosted desktop-info
python3 tools/chimera/chimera-hosted run --mode linux -- echo "hello from OctavianOS"
```

The hosted bridge runs as a process on the existing host OS; it is not a replacement kernel, full Windows/Linux syscall emulator, or bare-metal guest. CI smoke-tests its commands and configures the vendored native-toolchain CMake project. Those checks do not prove that Koronos boots, Aurora launches as a native compositor, or guest ISA backends are conformant.

See [Chimera source integration and acceptance gates](docs/CHIMERA_SOURCE_INTEGRATION.md) for migration status, validation requirements, and the full-history import prerequisite. Full source-history import remains blocked until the repository owner configures the `OCTAVIANOS_IMPORT_TOKEN` secret with the documented least-privilege permissions and runs the import workflow.

## Native N-bit architecture

The architectural target is an 8192-bit default *software-defined* native execution model, configurable to N bits. It requires explicit-width integer/register abstractions, architecture profiles, ABI and memory-layout rules, and checked adapters for physical ISA backends. An 8192-bit register model does not imply that x86-64, ARM64, or other physical CPUs directly execute 8192-bit instructions; physical backends must lower, emulate, or trap unsupported operations honestly.

The implementation is not complete until arithmetic/flags, decoding, memory addressing, exceptions/traps, privilege, context switching, and conformance tests pass for each declared profile.

## Engineering gates

Do not claim a target GUI or installer works until the boot menu target, staged payload, kernel handoff, userspace entry, and GUI process have been traced and exercised in automated boot tests. Do not mark an ISA as implemented based only on a catalog entry or metadata.


## Engineering notes

- [Migration runbook](docs/MIGRATION_RUNBOOK.md) — required GitHub token permissions and history-preserving import procedure.
- [Boot target audit](docs/BOOT_TARGET_AUDIT.md) — source-level target-to-payload trace and QEMU acceptance gates.
- [Native N-bit model](docs/architecture/NBIT_NATIVE_MODEL.md) — configurable register substrate, tests, and limitations.


## Installer routing correction

The top-level GRUB installer menu now routes to `/boot/jasper/install.cfg` rather than passing the Live initramfs as installer media. The dedicated Jasper path checks for the installation image, manifest, contract, phase list and profile list; if required media is missing, the menu fails closed instead of booting Live as Installer.

- Change: [PR #2](https://github.com/amerhwitat/OctavianOS/pull/2) — merged.
- Static regression CI: [installer routing workflow](https://github.com/amerhwitat/OctavianOS/actions/workflows/installer-routing.yml).
- Remaining: import full source/assets, rebuild ISO, validate staged file paths, execute the installer userspace, and observe the Aurora Installer GUI-ready marker in QEMU. Static menu checks do not prove these runtime stages.


## Desktop environments and artwork

- [Aurora Wayland Glass Desktop prototype](desktop/aurora-wayland-glass/index.html) — macOS-inspired global menu bar, glass windows and centered dock. Aurora's product name and existing artwork contract remain unchanged.
- [Marine Desktop prototype](desktop/marine/index.html) — Windows-style centered taskbar, Start menu, desktop shortcuts and ocean wallpaper.
- [Wallpaper catalog and license notes](desktop/artwork/README.md) — remote Unsplash image sources, attribution, license references and offline packaging requirements.
- [Desktop layout and session contract](docs/DESKTOP_ENVIRONMENTS.md) — native/compatibility/VM/remote session boundaries.

These HTML pages are interactive design prototypes, not native Wayland compositors or proof that session launch works. The current wallpapers are remotely hosted; offline ISO packaging must import, checksum, and stage approved assets through the existing artwork contract. Static contract tests are in `tests/desktop/` and run through the Desktop artwork and layout contracts workflow.


## Boot target trace

The source-level GRUB/Jasper routing graph is documented in [docs/BOOT_SEQUENCE_TRACE.md](docs/BOOT_SEQUENCE_TRACE.md), with the current status and runtime gates in [docs/BOOT_TARGET_AUDIT.md](docs/BOOT_TARGET_AUDIT.md). The boot-routing workflow parses tracked GRUB scripts and checks that every `configfile` edge resolves to a tracked config. Live CD menu entries distinguish Aurora Wayland Glass Desktop from Marine Desktop. These checks do not prove that generated ISO payloads are present or that Koronos executes userspace; ISO and QEMU acceptance remain required.

The staged ISO payload validator is [tools/boot/validate_iso_payloads.py](tools/boot/validate_iso_payloads.py). Run it against an extracted or staged ISO tree before publishing: `python3 tools/boot/validate_iso_payloads.py --root <iso-root>`. It checks required target payloads, x86_64 ELF identity and Multiboot2 header checksum; it does not replace QEMU boot testing.

## Original OctavianOS artwork

`desktop/aurora/assets/octavian-octopus-aurora.svg` is original project artwork for the Aurora desktop: a bioluminescent octopus beneath aurora ribbons over a deep-ocean horizon. Its metadata is in `desktop/aurora/assets/octavian-artwork-manifest.json`. It is a desktop SVG source asset; GRUB firmware-stage display is not claimed until the ISO builder generates and embeds a PNG/JPEG derivative and validates it inside the ISO.

ISO release policy and required QEMU evidence are documented in [docs/ISO_RELEASE_ACCEPTANCE.md](docs/ISO_RELEASE_ACCEPTANCE.md). A successful source build or kernel-entry marker is not production acceptance.
