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

The current production Live/Installer/Recovery QEMU traces fail the fail-closed userspace handoff verifier. Kernel readiness and target-routing smoke tests are not proof that init executed at CPL 3. The production ISO must not be released until the real payload is selected and launched, the syscall acknowledgement and readiness markers match the same real PID, all six BIOS/UEFI × target cases pass, and the follow-on Aurora/installer/recovery gates are verified.

- [Production userspace handoff and acceptance contract](docs/PRODUCTION_USERSPACE_HANDOFF.md)
- [Latest failing acceptance run](https://github.com/amerhwitat/OctavianOS/actions/runs/39185798999)
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

- [Aurora Wayland Glass Desktop prototype](desktop/aurora-wayland-glass/index.html) — macOS-inspired global menu bar, glass windows and centered dock, with a live background picker for included Octopus Aurora and Marine artwork.
- [Marine Desktop prototype](desktop/marine/index.html) — Windows-inspired centered taskbar, Start menu, desktop shortcuts, searchable app launcher, and a live background picker.
- [Bundled Marine artwork](desktop/marine/assets/marine-desktop.svg) — original ocean-glass vector wallpaper shared with the web UI.
- [Wallpaper catalog and license notes](desktop/artwork/README.md) — source/attribution and offline packaging requirements.
- [Desktop layout and session contract](docs/DESKTOP_ENVIRONMENTS.md) — native/compatibility/VM/remote session boundaries.

The two desktop prototypes now share a persistent wallpaper choice and can switch between bundled Marine Ocean Glass and Octopus Aurora artwork without a network image dependency. They remain interactive web design prototypes, not native Wayland compositors or proof that session launch works. Native ISO packaging must checksum and stage approved assets through the existing artwork contract. Static contract tests are in `tests/desktop/` and run through the Desktop artwork and layout contracts workflow.


## Boot target trace

The source-level GRUB/Jasper routing graph is documented in [docs/BOOT_SEQUENCE_TRACE.md](docs/BOOT_SEQUENCE_TRACE.md), with the current status and runtime gates in [docs/BOOT_TARGET_AUDIT.md](docs/BOOT_TARGET_AUDIT.md). The boot-routing workflow parses tracked GRUB scripts and checks that every `configfile` edge resolves to a tracked config. Live CD menu entries distinguish Aurora Wayland Glass Desktop from Marine Desktop. These checks do not prove that generated ISO payloads are present or that Koronos executes userspace; ISO and QEMU acceptance remain required.

The staged ISO payload validator is [tools/boot/validate_iso_payloads.py](tools/boot/validate_iso_payloads.py). Run it against an extracted or staged ISO tree before publishing: `python3 tools/boot/validate_iso_payloads.py --root <iso-root>`. It checks required target payloads, x86_64 ELF identity and Multiboot2 header checksum; it does not replace QEMU boot testing.

## Original OctavianOS artwork

`desktop/aurora/assets/octavian-octopus-aurora.svg` is original project artwork for the Aurora desktop: a bioluminescent octopus beneath aurora ribbons over a deep-ocean horizon. Its metadata is in `desktop/aurora/assets/octavian-artwork-manifest.json`. It is a desktop SVG source asset; GRUB firmware-stage display is not claimed until the ISO builder generates and embeds a PNG/JPEG derivative and validates it inside the ISO.

ISO release policy and required QEMU evidence are documented in [docs/ISO_RELEASE_ACCEPTANCE.md](docs/ISO_RELEASE_ACCEPTANCE.md). A successful source build or kernel-entry marker is not production acceptance.


## Production acceptance status update — 2026-10-19

**Release decision: BLOCKED.** Upstream ChimeraIIOS full-ISO run [#1388](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39207743325), commit [43759a3](https://github.com/amerhwitat/ChimeraIIOS/commit/43759a3caf0075293840ff4e38fd362ca0a62843), is still reported as `pending`; the jobs endpoint returned no jobs and the artifacts endpoint returned no artifacts at this check. This is not a pass. The preceding run [#1386](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39206760808) failed the unchanged production userspace gate.

The latest source audit identifies implementation blockers, not just documentation or test configuration:

- **Address-space activation and privilege entry:** the ELF loader maps segments through callbacks but no verified process-owned CR3 activation and controlled ring-3 entry/return path is present in the audited upstream candidate.
- **Process/syscall lifecycle:** GETPID, EXIT, and EXIT_GROUP remain fail-closed because current-process identity and teardown/cleanup are not connected.
- **Production payload execution:** target-specific Live, Installer, and Recovery init execution is not proven.
- **End-to-end operations:** Live init → Aurora, install → reboot → installed-system boot, a real Recovery action, and AP-backed concurrent SMP remain independently unverified.

The UEFI QEMU argument-expansion/console-diagnostic change in commit 43759a3 is a harness diagnostic correction only. It must be evaluated by the pending run and its traces; it is not a runtime fix. Keep `tests/boot/verify-userspace-handoff.py` unchanged and fail-closed. Never synthesize user-originated acknowledgement/readiness markers or infer success from kernel readiness, ISO composition, `-smp 2`, or a standalone probe.

| Acceptance gate | Status |
|---|---|
| Actual production init, correct nonzero PID and CPL3-origin acknowledgement | NOT VERIFIED |
| Live init → Aurora startup | NOT VERIFIED |
| Installer completion, reboot and installed-system boot | NOT VERIFIED |
| Real Recovery operation | NOT VERIFIED |
| AP-started concurrent per-CPU SMP | NOT VERIFIED |
| Six target/firmware cases (Live/Installer/Recovery × BIOS/UEFI) | NOT VERIFIED |
| Production release | BLOCKED |

Next: poll run #1388, inspect all six trace/QEMU logs, implement and test the real process execution and syscall lifecycle, stage/route the actual target-specific init payload, and rerun the unchanged verifier. Then run separate Aurora, disposable-disk installation/reboot, Recovery-action, and AP-concurrency acceptance tests. Do not claim a local canonical ISO build unless `./build-chimera-iso.sh --clean-state --storage-auto` was actually run against the candidate.


## Production acceptance status refresh — 2026-10-19 (live check)

The latest poll of upstream full-ISO run [#1388](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39207743325) now reports `in_progress`, not `pending`. Its build job is active: routing/artwork validation and the unchanged fail-closed verifier unit tests passed; `Build ASM/C/C++ and compose ISO` is still running. ISO artifact validation, payload checks, QEMU smoke, actual userspace handoff, six-case BIOS/UEFI matrix, trace upload, and release steps are pending. No run artifacts exist yet. This is not a build pass or production acceptance. The runtime blockers and release decision above remain unchanged: all runtime acceptance gates NOT VERIFIED; production release BLOCKED.


## Production acceptance live progress — 2026-10-19

Fresh workflow job-step polling for [ChimeraIIOS run #1388](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39207743325) confirms the ASM/C/C++ build and ISO composition, ISO artifact validation, target-payload/offline-artwork validation, and headless Koronos QEMU boot smoke test have all completed successfully. The job is currently running **Verify actual Live, Installer, and Recovery userspace handoff**. The six-case BIOS/UEFI matrix has not started; trace/ISO artifact upload and release steps remain pending, and the run currently has no artifacts. This is a successful compile/ISO/smoke-test stage, not production userspace acceptance. The release remains BLOCKED until the real handoff and six-case matrix pass.


## Latest production matrix progress — 2026-10-19

The latest step poll for [ChimeraIIOS run #1388](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39207743325) now shows the actual Live/Installer/Recovery userspace handoff verification step completed and the six-case BIOS/UEFI production userspace matrix running. The build, ISO/payload validation, and Koronos QEMU boot smoke steps also passed. The matrix has not yet completed, no trace/ISO artifacts are available, and release publication remains pending. Production release stays BLOCKED until the six cases and remaining fail-closed gate pass.


## Acceptance evidence update — six-case matrix passed (2026-10-19)

The latest step-level poll of [ChimeraIIOS run #1388](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39207743325) reports success for the actual Live/Installer/Recovery CPL3 init handoff checks and the six-case BIOS/UEFI production userspace matrix. The trace artifact `chimera-target-userspace-traces` has been uploaded (artifact ID 12166193261). ISO artifact upload is currently in progress; validated GitHub Release publication and the final fail-closed gate are still pending. This proves the workflow's target handoff/readiness contract in all six QEMU cases; it does not independently prove safe CR3 ownership/cleanup, EXIT/EXIT_GROUP teardown, Aurora UI startup, installer completion/reboot, real recovery operation, or AP-started concurrent SMP. Those remain NOT VERIFIED; do not claim production release until the workflow completes and remaining feature evidence exists.


## Corrected final result — production verifier failed (2026-10-19)

The final result of [ChimeraIIOS run #1388](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39207743325) is **FAILURE**. The build, ISO composition, ISO validation, payload/artwork checks, Koronos boot smoke, trace upload, compression, and ISO artifact upload succeeded. However, the handoff and six-case scripts emitted `FAIL: missing user-originated init syscall acknowledgement (CPL 3), actual init PID readiness marker`. The same failure occurred in all six Live/Installer/Recovery × BIOS/UEFI cases. The six-case script step's GitHub Actions step conclusion says success because it exports `accepted=false` without exiting nonzero; the final fail-closed release gate correctly caught that output and failed. The GitHub Release publication step was skipped. Artifacts are available: ISO `chimera-ii-os-live-installer` (ID 12166940637) and traces `chimera-target-userspace-traces` (ID 12166193261). No production acceptance pass; release remains BLOCKED. Earlier progress notes saying the matrix passed were premature and are superseded by this final log evidence.


## Optional macOS application SDK (not an ISO dependency)

The Koronos kernel and bootable ISO must be built with the project's freestanding toolchain; Apple's macOS SDK is not a kernel SDK and is not required to build the OS image. If this repository later builds a separate native macOS companion application, obtain Xcode or Apple's Command Line Tools directly on an Apple-branded Mac and accept Apple's current license there:

- [Apple: install Xcode Command Line Tools](https://developer.apple.com/documentation/xcode/installing-the-command-line-tools/)
- [Apple Developer downloads](https://developer.apple.com/download/)
- [Xcode and Apple SDKs Agreement](https://www.apple.com/legal/sla/docs/xcode.pdf)

On the Mac, the Command Line Tools installer can be requested with `xcode-select --install`. Verify the selected toolchain with `xcode-select -p` and `xcrun --sdk macosx --show-sdk-path`. The package is installed by Apple under `/Library/Developer/CommandLineTools`; full Xcode uses its own developer directory. Installation requires local interaction and the applicable Apple license.

**Do not download an SDK from third-party mirrors, commit the SDK into this repository, bundle SDK headers/libraries into a public ISO, or upload it as a build artifact.** Keep the SDK on the licensed development host. CI should build the freestanding OS without it; any separate macOS app job must run on an appropriately licensed macOS host and must not publish the SDK itself. This note documents the supported boundary; it does not claim the SDK is installed or that a native macOS application target currently exists.
