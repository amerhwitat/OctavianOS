# N-bit and Hosted Compatibility Modes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users choose among validated software N-bit profiles and supported Linux, Windows, and macOS compatibility routes, with each mode's actual execution backend visible on the desktop.

**Architecture:** Keep software-defined N-bit arithmetic separate from physical ISA execution. Extend the existing architecture/support matrix and mode policies, expose only tested profiles through desktop controls, and route hosted applications through explicit web, native-host, VM, remote, or compatibility adapters.

**Tech Stack:** C/C++ N-bit substrate; JSON policy and support matrix; desktop HTML/JavaScript UI; Linux/Windows/macOS build runners; QEMU for architecture smoke tests.

**Spec:** `docs/superpowers/specs/2026-11-03-production-first-vertical-slices-design.md`

## Global Constraints

- Default 8192-bit software register model does not mean physical x86_64/ARM64 CPUs execute 8192-bit instructions.
- A profile may be selectable only when arithmetic, flags, decoder, memory/fault behavior, privilege, context switching, and conformance checks exist for its declared scope.
- Windows/macOS integration uses authorized host APIs, licensed host images, or app/web/VM/remote routes; no proprietary system files are bundled.
- All desktop modes display backend type, architecture, limitations, and permission requirements.
- Never load an architecture's kernel or userspace payload on another architecture without a verified translation/VM path.

## Review Focus

- Requested bit width absent from compiled profiles — reject and retain the current profile.
- Host API unavailable — show a disabled capability with supported route rather than a broken button.
- User changes mode while an app is running — preserve process isolation and require a documented restart if needed.
- Unsupported CPU architecture selected — refuse to boot/load its image.
- Licensing or user-provided OS image absent — keep VM option unavailable.

---

### Task 1: Make N-bit selectable profiles evidence-backed

**Files:**
- Modify: `OctavianOS/include/octavian/nbit.h`
- Modify: `OctavianOS/architecture/support-matrix.json`
- Modify: `OctavianOS/tests/nbit/test_nbit.c`
- Modify: `OctavianOS/tests/architecture/test_support_matrix.py`
- Mirror: `ChimeraIIOS` N-bit definitions and tests
- Create: `OctavianOS/architecture/nbit-profiles.json`

**Interfaces:**
- Consumes: N-bit substrate and architecture backend registry.
- Produces: `nbit_profile_select(profile_id) -> status` (or the existing equivalent API) accepting only compiled/tested profiles and returning the supported bit width plus backend kind.

- [ ] **Step 1: Add failing tests** for supported profile selection, unsupported-width rejection, overflow/flag behavior, and normalization.
- [ ] **Step 2: Run** the existing N-bit workflow compile/run command (`cc -std=c11 -Wall -Wextra -Werror -pedantic -Iinclude tests/nbit/test_nbit.c`) across its width matrix and the architecture support pytest in both repos. Expected: new profile-selection tests fail before implementation.
- [ ] **Step 3: Implement profile validation** and separate “software width” from “physical ISA” in the API and manifest.
- [ ] **Step 4: Re-run** C and Python checks. Expected: only validated software profiles are selectable.
- [ ] **Step 5: Commit** profile metadata and API changes in both OS repos.

### Task 2: Add hosted Linux/Windows/macOS adapter records

**Files:**
- Modify: `OctavianOS/architecture/support-matrix.json`
- Modify: `OctavianOS/desktop/upstream_desktop_feature_matrix.json`
- Modify: `ChimeraIIOS/desktop/platform_profiles.json`
- Modify: `ChimeraIIOS/desktop/desktop_profiles.json`
- Modify: hosted compatibility adapters under `ChimeraIIOS/tools/runtime/` and `OctavianOS/tools/chimera/`
- Create: platform profile tests under existing `tests/architecture/`

**Interfaces:**
- Consumes: existing `native`, `virtual-machine`, `instruction-emulation`, and `compatibility-layer` route types.
- Produces: per-OS and per-app mode state `supported`, `partial`, or `unavailable`, with a concrete runtime route and limitations.

- [ ] **Step 1: Add tests** for native-vs-hosted route labels, unsupported host APIs, unlicensed VM image absence, and architecture mismatch.
- [ ] **Step 2: Run** `python -m pytest -q tests/architecture/test_support_matrix.py` and hosted bridge tests in both repos. Expected: unverified modes remain `release_supported: false`.
- [ ] **Step 3: Implement host adapter probing** for installed runtime/API capabilities and connect it to the existing compatibility mode control; do not emulate APIs that are not implemented.
- [ ] **Step 4: Re-run** profile tests and platform builds on Linux, Windows, and macOS runners available in the linked workflows.
- [ ] **Step 5: Commit** adapter/profile changes and record per-runner evidence.

### Task 3: Expose truthful desktop mode selection

**Files:**
- Modify: session app panels and runtime modules produced by `2026-11-03-desktop-sessions-voiceconnect-plan.md`
- Modify: both desktop app registries and mode profile JSON files
- Add: UI contract tests in each OS repository

**Interfaces:**
- Consumes: validated N-bit and host compatibility profile IDs from Tasks 1–2.
- Produces: `selectMode(modeId)` that persists only a validated choice and displays its width/backend/capability status.

- [ ] **Step 1: Add failing UI tests** for mode labels, persistence, unsupported-option disabling, keyboard access, and safe fallback after corrupt preference data.
- [ ] **Step 2: Run** the desktop session UI tests from the first plan. Expected: the mode control is missing or accepts unknown profiles.
- [ ] **Step 3: Connect the mode chooser** to validated manifests, display backend and limits, and require restart only where the active runtime needs it.
- [ ] **Step 4: Re-run** UI tests in both OS repos and build both live ISOs.
- [ ] **Step 5: Commit** mode UI and profile data; publish no platform-support claim beyond the passing matrix.

