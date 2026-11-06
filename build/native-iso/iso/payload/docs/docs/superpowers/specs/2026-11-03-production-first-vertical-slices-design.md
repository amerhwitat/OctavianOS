# Production-first vertical slices — design

Date: 2026-11-03

## Intent

Make the ChimeraIIOS and OctavianOS desktop experience more useful by connecting desktop controls to real application launch routes, adding VoiceConnect from `amerhwitat/test` to both ISO app panels, and advancing Live, Installer, and Recovery targets through their actual boot and runtime acceptance gates. The named desktop gallery should remain an honest, attractive browser preview and expose working controls where a compatible implementation exists.

## Goals

- Deliver Aurora, Marine, Seelen UI, Koronos Workbench, Nova, and Mobile Edition as selectable, runnable desktop sessions in both ISO projects, each with a consistent, visible Applications panel, taskbar/dock, compatibility status, and event handling.
- Add VoiceConnect P2P, sourced from `amerhwitat/test` branch `feat/voiceconnect-p2p-camera` at a pinned revision, to both OS desktop app panels and package the real app into both Linux live images after its Linux build and runtime can be reproduced.
- Inventory applications, commands, Python/Java code, package managers, and candidate drivers from the repositories referenced by the existing Chimera/Octavian application catalogs and integration manifests. Distinguish integrated, buildable, preview-only, blocked, and unsupported items.
- Keep Live, Installer, and Recovery distinct in GRUB/Jasper/Gates menus and validate their payload selection and execution rather than accepting menu labels or ISO composition as proof.
- Expose N-bit/research architecture choices only for implemented, validated execution profiles; clearly distinguish software emulation/lowering from physical CPU capabilities.
- Build and publish progress in small, reviewable changes to the relevant source repositories and update release/site status only after the corresponding CI gates pass.

## Non-goals and anti-goals

- Do not promise every app in every GitHub repository builds for every OS or CPU. The source set is bounded by the explicitly named OS/VoiceConnect repositories plus application-bearing repositories already enumerated by the project manifests and catalogs; the inventory step records gaps and access/license limits.
- Do not copy Windows/macOS system code, proprietary assets, or OS images. Windows and macOS profiles describe supported hosted, virtualized, remote, web, or compatibility routes only.
- Do not claim a desktop concept, catalog record, successful compile, or screenshot proves native compositor/session support. A runnable session in the current Linux live ISO is a Linux-hosted session; Koronos Workbench remains a research profile until the native Koronos route passes its gates.
- Do not claim generic support for every physical device. Driver work is limited to devices represented in the repositories and declared target matrix, with each device marked at its actual evidence level.
- Do not silently run compatibility apps with unrestricted shell, file, network, or device access. App actions use explicit manifests/permissions and safe launch APIs.
- Do not make sounds mandatory: sound feedback is opt-in, respects mute/reduced-motion/accessibility preferences, and is secondary to visible state.

## Current project evidence and constraints

- ChimeraIIOS contains desktop app registries, desktop/platform profiles, UI command/control contracts, command catalogs, and several Aurora implementations. These artifacts provide integration points but do not prove each app/profile is runnable.
- OctavianOS declares Aurora Wayland Glass and Marine as first-party desktop identities and has separate Jasper configs for Live, Installer, Recovery, and Diagnostics. Its desktop contract warns that external desktops require an explicit native, VM, container, remote, compatibility, or web route.
- OctavianOS documents that production Live/Installer/Recovery handoff is still fail-closed until a real CPL3 init syscall/readiness trace and follow-on desktop/installer/recovery gates pass. A prior production userspace trace failed this gate.
- Current live image builder produces Debian Linux images. It stages the OS desktop payload; it is not a native Koronos image.
- VoiceConnect P2P lives at `amerhwitat/test/voiceconnect-p2p/` on branch `feat/voiceconnect-p2p-camera`, not on the default `main` branch. The branch tip inspected for this design is `c3f0df816099b042486f5c5ec4405e2690690dc8`; the app requires Node >=24 and can build Electron targets for Linux, Windows, and macOS. Its latest checked CI on that tip built Linux/macOS successfully but failed the Windows desktop job at “Verify real Windows mouse clicks through Chromium input dispatch” (run `41468889390`). The release-gate record still says preview-only, with no production deployment; macOS output is unsigned. Pin and build the exact source revision, correct the failing Windows acceptance gate, and keep service availability, camera/microphone consent, and STUN/TURN configuration visible in the UI. Do not bundle credentials or claim a production signaling service.
- Chimera/Octavian catalog entries frequently remain `catalog-only`. Catalog metadata must not be converted into a “supported” claim without provenance, dependency/license review, reproducible build, and runtime verification.

## Approaches considered

1. **Production-first vertical slices — selected.** Connect real desktop actions and app launchers, stage verified applications into both images, then advance boot/installer/recovery one traceable target at a time. This aligns screen behavior with OS execution evidence and can publish incremental releases.
2. **Inventory/build matrix first.** Exhaustively map applications/platforms/runners before changing product behavior. This provides broad visibility but delays the requested desktop and VoiceConnect integration; retain a focused inventory as the first task within approach 1.
3. **Showcase-only implementation.** Improve browser mockups and launcher appearance while deferring actual packages and boot targets. Fastest visually, but fails the user's production-first choice and risks overstating compatibility.

## Proposed delivery sequence

### Slice 0 — acceptance inventory and source provenance

- Read the project app/session/driver/command registries and referenced repository manifests.
- Create a cross-repository matrix with owner/source URL, exact source revision, license/provenance, language/runtime, target architecture, dependencies, build workflow/runner, package status, desktop launch path, and evidence level.
- Capture current CI and boot acceptance states. Do not change unsupported catalog records to supported.

### Slice 1 — six runnable sessions, desktop app panels, and VoiceConnect

- Define or reconcile one app-launch contract across ChimeraIIOS and OctavianOS: stable ID, visible name/category, source and version, runtime/architecture, launch method/URI, permission declarations, readiness/health check, supported compatibility modes, and unavailable reason.
- Package six selectable session entrypoints in both ISO projects. Aurora and Marine preserve their first-party visual identities; Seelen UI, Koronos Workbench, Nova, and Mobile Edition become distinct, runnable experiences inspired by the supplied reference images. Each session declares its backend and limitations and can return safely to the session chooser.
- Make the taskbar/dock and Applications panel persistently visible and keyboard accessible in every session. Share behavior and accessibility rules while preserving each desktop identity and responsive layout.
- Add the N-bit/compatibility selector as a truthful capability view. It may select only a tested software profile; unavailable hardware/runtime choices remain visible with their route and limitation.
- Wire every interactive button to an action or an explicit disabled explanation. Add event feedback and opt-in sounds with mute/reduced-motion settings.
- Add VoiceConnect P2P from the pinned feature-branch revision to both app panels. Stage its source and runtime in both ISO build flows only after dependencies, license, launch path, user data, offline behavior, and isolation are confirmed. Resolve the Node >=24 requirement for the current Debian base reproducibly. The panel must distinguish local app startup from reachable signaling/STUN/TURN service readiness; request camera/microphone access only after user action.
- Build both app/desktop CI matrices, verify page controls and launch responses, build both Linux ISOs, select and start each of the six sessions from each ISO, exercise launcher routes in the actual images, and publish updated releases only after all six session cases pass.

### Slice 2 — boot menus, Live, Installer, and Recovery

- Keep GRUB/Jasper/Gates entries mapped to distinct target manifests and payloads; enforce file/hash/architecture checks and fail closed when a target payload is missing.
- Ensure Live starts a real user process and then launches the selected supported desktop. Recovery must reach an observable text/service shell even without graphics. Installer must inventory only the test disk, show a plan, require explicit confirmation, perform a reversible/contained QEMU installation, and reboot to the installed target.
- Validate BIOS/UEFI target matrices and real same-process CPL3 syscall/readiness evidence. Do not publish a “native Koronos installer/recovery” claim until the exact production target passes all gates.

### Slice 3 — packages, utilities, language runtimes, and drivers

- Build app batches from the source matrix, preserving each repository's own toolchain and licensing. Keep package managers scoped to their actual repository/package source, with signature/hash verification, rollback, and no implicit elevation.
- Port/build commands and Python/Java utilities only where dependencies and target runtimes are available. Provide task-manager/monitor panels backed by the actual process/service APIs on each execution route.
- Prioritize drivers present in the target hardware matrix (including virtual QEMU devices used by CI), then report tested device IDs, architectures, and functions. Broader device coverage is incremental, not a blanket “all drivers” claim.

### Slice 4 — hosted platform compatibility and desktop expansion

- Route Linux, Windows, and macOS desktop personalities through explicit hosted app, browser, VM, container, remote-session, or compatibility adapters with visible mode labels and permissions.
- Use only licensed host APIs and user-provided OS images where needed. Windows/macOS system images and proprietary files are never bundled.
- Expand desktop profiles and app coverage only when the matching route passes its build and interaction gates. The six named experiences are runnable in the Linux-hosted ISOs under Slice 1; native Koronos and Windows/macOS sessions remain separate claims requiring their own backend and acceptance evidence.

## Shared release and evidence rules

- CI validates registry schemas, manifest-to-file links, source revisions, duplicate IDs, launch-method permissions, package inclusion, command/event handlers, and supported-profile claims.
- Desktop acceptance checks visible controls, keyboard/focus behavior, persisted desktop/mode choices, mute/reduced-motion behavior, error/fallback states, and app launch/readiness.
- ISO acceptance checks GRUB/Jasper target routing, ISO payload hashes, BIOS/UEFI boot, Live CPL3 readiness, Recovery availability, and installer operation in disposable QEMU storage. Production claims require tests against the exact release commit/image.
- Keep Linux live image claims separate from native Koronos claims. Record failed checks without loosening fail-closed acceptance criteria.
- Publish only build outputs that passed their declared gates; link source commit, checksum, and evidence report from both repository READMEs and the portfolio downloads/gallery pages.

## Decisions already made / builder calls

- User selected **Production-first vertical slices**.
- User confirmed all six named environments should become selectable, runnable sessions in both ISO projects. Preserve Aurora and Marine as first-party desktop personalities and keep each session's backend label truthful.
- User confirmed the app inventory/build matrix is limited to application-bearing repositories referenced by the existing OS catalogs and manifests, rather than every repository in the GitHub portfolio.
- Use existing app/session/control contracts and current build systems before introducing a new framework or package manager.
- Treat exact per-slice repository ownership, supported app subset, tested emulated devices, and CI matrix as builder decisions to document in the source inventory before implementation.

## Approval requested

- Confirm the design delivers six selectable, runnable Linux-hosted ISO sessions in both projects while keeping native Koronos claims behind native boot and userspace evidence.
- Confirm app inventory scope is the explicitly named projects plus app-bearing repositories already referenced in the OS catalogs/manifests.
- Confirm the sequence starts with the six sessions and VoiceConnect, followed by production Live/Installer/Recovery gates, then app/runtime/driver batches and hosted Windows/macOS routes.

