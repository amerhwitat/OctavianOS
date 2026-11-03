# Six Desktop Sessions and VoiceConnect Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship six selectable desktop sessions with visible, working app panels in both Linux live ISOs, including a locally packaged VoiceConnect P2P app.

**Architecture:** Extend the existing fullscreen WebKit kiosk and session-selection input instead of introducing a second compositor. Keep session manifests and app action contracts in each OS repository, package each named HTML desktop, and expose VoiceConnect through its pinned Linux runtime. This creates real Linux-hosted ISO sessions while keeping native Koronos and other host compatibility claims separate.

**Tech Stack:** HTML/CSS/JavaScript; Python 3 GTK/WebKit kiosk; Debian Trixie live rootfs; GRUB; JSON; Node.js 24+; npm lockfile; GitHub Actions; Python `unittest`/pytest and QEMU.

**Spec:** `docs/superpowers/specs/2026-11-03-production-first-vertical-slices-design.md`

## Global Constraints

- The six session IDs are `aurora`, `marine`, `seelen-ui`, `koronos-workbench`, `nova`, and `mobile-edition`.
- The matching names are `Aurora Wayland Glass Desktop`, `Marine Desktop`, `Seelen UI Desktop`, `Koronos Workbench Desktop`, `Nova Desktop`, and `Mobile Edition`.
- Both ISO projects currently run Debian Linux with a fullscreen WebKit2GTK kiosk; this plan does not claim native Koronos session execution.
- VoiceConnect source is `amerhwitat/test` branch `feat/voiceconnect-p2p-camera`, pinned initially to commit `c3f0df816099b042486f5c5ec4405e2690690dc8`.
- VoiceConnect requires Node.js `>=24.0.0`; ISO build must pin and verify an available runtime and use `npm ci` with the committed lockfile.
- VoiceConnect is a networked P2P client. Do not package TURN credentials, persistent peer IP history, or a production signaling server. Ask for camera/microphone access only after user action.
- The current VoiceConnect Windows click-acceptance failure is open; don't mark the Windows desktop package accepted until its input-dispatch gate passes.
- Every app/control must map to a real supported launch/action or explain why it is unavailable. Catalog entries alone are not installed apps.
- ISO release publication requires the session matrix and packaged-app checks to pass against the exact source commit.

## Review Focus

- Missing, malformed, or unsupported session ID — reject it and enter the safe fallback rather than opening an arbitrary path.
- Missing session entrypoint or asset in the squashfs — fail the ISO payload check and do not publish.
- Missing VoiceConnect runtime/dependency or failed service startup — show a clear unavailable state and keep the desktop usable.
- VoiceConnect opened without network/signaling configuration — show local UI readiness separately from call readiness.
- Camera/microphone denied — keep audio/video controls accurate and do not keep retrying permissions.

---

### Task 1: Pin six session IDs and fail-closed selection

**Files:**
- Modify: `OctavianOS/boot/live/desktop-sessions.json`
- Modify: `OctavianOS/boot/jasper/live.cfg`
- Modify: `OctavianOS/desktop/sessions/session-manifest.schema.json`
- Modify: `ChimeraIIOS/web/desktop_profiles.json`
- Modify: `ChimeraIIOS/boot/live/desktop-sessions.json` (create if absent)
- Modify: `OctavianOS/tests/boot/test_boot_target_graph.py`
- Create: `OctavianOS/tests/desktop/test_desktop_session_contract.py`
- Create: `ChimeraIIOS/tests/desktop/test_desktop_session_contract.py`

**Interfaces:**
- Consumes: Existing `chm.desktop=<id>` live selection and existing GRUB live-menu routing.
- Produces: Stable session IDs and entrypoint paths consumed by the kiosk selector and app panel.

- [ ] **Step 1: Add failing session contract checks** for exactly the six IDs, unique names, in-payload entrypoints, supported backend labels, and rejection of unknown IDs.
- [ ] **Step 2: Run** `python -m pytest -q tests/desktop/test_desktop_session_contract.py tests/boot/test_boot_target_graph.py` in both repositories. Expected: fail because the current Octavian contract only defines Aurora and Marine and Chimera has no six-session ISO map.
- [ ] **Step 3: Add the six manifest records** to both OS sources. Define each `id`, exact display `name`, `entrypoint`, `runtime: "linux-webkit-session"`, `architecture: ["x86_64"]`, and a capability/status label; mark Mobile Edition as a responsive x86_64 session, not ARM64 boot support.
- [ ] **Step 4: Re-run the focused contract checks.** Expected: all six IDs validate; unknown IDs and missing entrypoints fail closed.
- [ ] **Step 5: Commit** the manifests and focused tests in the two OS repositories.

### Task 2: Build the six distinct desktop surfaces and shared app panel

**Files:**
- Modify: `OctavianOS/desktop/aurora-wayland-glass/index.html`
- Modify: `OctavianOS/desktop/marine/index.html`
- Create: `OctavianOS/desktop/seelen-ui/index.html`
- Create: `OctavianOS/desktop/koronos-workbench/index.html`
- Create: `OctavianOS/desktop/nova/index.html`
- Create: `OctavianOS/desktop/mobile-edition/index.html`
- Create: `OctavianOS/desktop/session-runtime.js`
- Modify: `ChimeraIIOS/web/aurora_3d_desktop.html`
- Modify: `ChimeraIIOS/web/aurora_3d_desktop.js`
- Modify: `ChimeraIIOS/web/aurora_apps.json`
- Modify: `ChimeraIIOS/web/desktop_profiles.json`
- Create: `ChimeraIIOS/web/session-runtime.js`
- Modify: desktop session test files from Task 1

**Interfaces:**
- Consumes: Session manifest IDs/entrypoints from Task 1.
- Produces: `window.OctavianSessionRuntime.launchApp(id)` and `window.ChimeraSessionRuntime.launchApp(id)`, resolving only allowlisted app records and exposing the same visible capability state.

- [ ] **Step 1: Add failing UI behavior checks** that assert an always-visible Applications button, taskbar/dock, desktop switcher, compatibility-mode status, keyboard-open/search/close behavior, and one action for every enabled app entry.
- [ ] **Step 2: Run** `python -m pytest -q tests/desktop/test_desktop_session_contract.py` in each repository. Expected: fail for missing panels/session surfaces.
- [ ] **Step 3: Implement the shared session runtime and panels** across the six pages. Use the attached reference identities/names, responsive layout, keyboard focus/escape behavior, reduced-motion support, and opt-in event sounds with a mute control. Display the current backend and compatibility route on every session.
- [ ] **Step 4: Re-run the UI/manifest checks.** Expected: all six pages have working app panel controls, no enabled dead controls, and each switch resolves to a known entrypoint.
- [ ] **Step 5: Commit** the desktop runtime and pages in both OS repositories.

### Task 3: Package and launch VoiceConnect P2P

**Files:**
- Modify: `OctavianOS/apps/desktop-application-catalog.json`
- Modify: `OctavianOS/live-image/build.sh`
- Modify: `OctavianOS/live-image/lib/aurora-kiosk.py`
- Modify: `ChimeraIIOS/web/aurora_apps.json`
- Modify: `ChimeraIIOS/live-image/build.sh`
- Modify: `ChimeraIIOS/live-image/lib/aurora-kiosk.py`
- Modify: both ISO builder workflows (`.github/workflows/live-image-build.yml` in each repository)
- Create or modify: `tests/live-image/test_voiceconnect_bundle.sh` in each repository
- VoiceConnect source: `amerhwitat/test/voiceconnect-p2p/{package.json,package-lock.json,server.js,index.html}` at the pinned revision

**Interfaces:**
- Consumes: App launch contract and desktop panel from Task 2.
- Produces: `voiceconnect-p2p` launch route to the local UI and service health status; the service listens only as configured by the app and never exposes secrets through the panel.

- [ ] **Step 1: Add failing bundle checks** for pinned source revision, Node version >=24, lockfile install, required app assets, launcher metadata, and healthy local server response.
- [ ] **Step 2: Run** `bash tests/live-image/test_voiceconnect_bundle.sh` in each OS repository. Expected: fail because no VoiceConnect files/runtime are staged yet.
- [ ] **Step 3: Add the Linux build dependency** that checks out/downloads the exact `test` source revision, verifies its revision and source integrity, installs production dependencies with `npm ci --omit=dev`, and stages the app plus a verified Node 24 runtime or an equivalently reproducible Linux package. Modify the generated `aurora-session` block in each `live-image/build.sh`, add an on-demand desktop launcher/service health adapter, and append a VoiceConnect app entry to both panels.
- [ ] **Step 4: Re-run bundle checks and the VoiceConnect Linux workflow** at the pinned source. Expected: app is present in both staged payloads and its local UI responds; external signaling/call readiness remains separately labeled.
- [ ] **Step 5: Commit** app registry, staging, launch adapter, and workflow changes in each OS repository; record the VoiceConnect source commit in both release manifests.

### Task 4: Select each session from the actual ISO

**Files:**
- Modify: `OctavianOS/live-image/build.sh`
- Modify: `ChimeraIIOS/live-image/build.sh`
- Modify: both `tests/live-image/test-aurora-fullscreen.sh`
- Create: `tests/live-image/test-six-desktop-sessions.sh` in each OS repository
- Modify: both `.github/workflows/live-image-build.yml`

**Interfaces:**
- Consumes: Session manifests, desktop pages, and VoiceConnect app package from Tasks 1–3.
- Produces: GRUB entries `live-aurora`, `live-marine`, `live-seelen-ui`, `live-koronos-workbench`, `live-nova`, and `live-mobile-edition`; `aurora-session` validates `chm.desktop` and sets `AURORA_DESKTOP_URI` to its allowlisted in-ISO entrypoint.

- [ ] **Step 1: Add failing ISO contract checks** asserting six GRUB entries, each entry passing a matching session ID, all six HTML entrypoints staged into squashfs, and no unsafe path interpolation.
- [ ] **Step 2: Run** `bash tests/live-image/test-six-desktop-sessions.sh` and the boot routing pytest. Expected: fail with the current four missing menu paths/entrypoints.
- [ ] **Step 3: Update GRUB generation and `aurora-session`** to route each ID from `/proc/cmdline` through the validated manifest; unrecognized/missing sessions must enter the existing safe text fallback. Preserve the classic X, safe graphics, verbose boot, reboot, and shutdown options.
- [ ] **Step 4: Re-run the session contract checks and build** both ISO images through their existing `live-image-build.yml` workflows. Expected: both builds include all six selectable sessions and the VoiceConnect package.
- [ ] **Step 5: Boot each session in QEMU** at 1280×720 and 1920×1080, verify visible/keyboard-operable app panels, switcher, and fallback behavior, then record per-session evidence and checksums.
- [ ] **Step 6: Commit and publish** only after the six-session matrix and VoiceConnect package gates pass; update both READMEs and the portfolio download index with exact run, commit, and checksum links.

---

## Independent follow-up plans

- `2026-11-03-native-boot-installer-recovery-plan.md` — Koronos/Spit Fire/Jasper/Gates production Live, Installer, and Recovery handoffs.
- `2026-11-03-applications-runtimes-packaging-plan.md` — source-backed app, command, Python/Java, package manager, and task manager integration from the catalog/manifests.
- `2026-11-03-driver-matrix-plan.md` — evidence-based drivers for the declared virtual and physical device targets.
- `2026-11-03-compatibility-nbit-plan.md` — selectable validated N-bit profiles and hosted Linux/Windows/macOS compatibility routes.

