# Native Boot, Installer, and Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make native Koronos Live, Installer, and Recovery boot paths execute real userspace in the supported BIOS/UEFI matrix before any native production claim.

**Architecture:** Preserve the separate native Koronos boot path and fail-closed GRUB/Jasper target configs. Trace one actual selected CPL3 init process through syscall acknowledgement and readiness markers per target; then add observable Aurora/Recovery/Installer behavior without substituting the Debian live image.

**Tech Stack:** GRUB 2/Jasper; Multiboot2; Koronos ELF; x86_64; C/C++; Python acceptance verifier; initramfs; QEMU BIOS/UEFI.

**Spec:** `docs/superpowers/specs/2026-11-03-production-first-vertical-slices-design.md`

## Global Constraints

- Live, Installer, and Recovery use distinct kernel arguments, initramfs/manifests, and payload checks.
- Native production acceptance needs real CPL3 init syscall acknowledgement and readiness markers tied to the same real PID across BIOS/UEFI and all three targets.
- The published Debian live ISO is a separate Linux route and cannot satisfy native Koronos acceptance.
- Do not weaken release gates, synthesize readiness markers, or claim successful disk installation from static GRUB checks.
- Installer writes only to an explicitly selected disposable QEMU test disk until destructive storage behavior has independent review and explicit user confirmation.

## Review Focus

- Missing installer/recovery modules — reject route before kernel handoff.
- Kernel enters but target init does not make a CPL3 syscall — acceptance fails closed.
- Init/readiness markers come from different PIDs or stale logs — acceptance fails.
- Graphics failure — Recovery must still provide a usable text/service shell.
- Installer abort or interrupted write — return an actionable error and preserve the test image's recovery path.

---

### Task 1: Pin exact production trace failure in tests

**Files:**
- Modify: `OctavianOS/tests/migration/test_userspace_handoff_verifier.py`
- Modify: `OctavianOS/tests/migration/verify-userspace-handoff.py`
- Mirror: corresponding native Koronos verifier/tests in `ChimeraIIOS`

**Interfaces:**
- Consumes: Current trace fields, target manifest, and actual child process/PID.
- Produces: One acceptance result that names missing CPL3 syscall, readiness, PID mismatch, target, and firmware mode distinctly.

- [ ] **Step 1: Add verifier regression cases** for no syscall ack, missing readiness, PID mismatch, target mismatch, stale marker, and successful same-PID trace.
- [ ] **Step 2: Run** `python -m pytest -q tests/migration/test_userspace_handoff_verifier.py` and corresponding Chimera tests. Expected: expose any verifier false acceptance and retain the known production failure.
- [ ] **Step 3: Implement strict trace matching** without changing pass conditions or allowing progress text as evidence.
- [ ] **Step 4: Re-run** the verifier suite. Expected: malformed traces fail and a same-PID real syscall/readiness trace passes.
- [ ] **Step 5: Commit** matching verifier behavior in both repositories.

### Task 2: Make all six boot-target matrices explicit and fail closed

**Files:**
- Modify: `OctavianOS/boot/iso/grub.cfg`
- Modify: `OctavianOS/boot/jasper/jasper.cfg`
- Modify: `OctavianOS/boot/jasper/live.cfg`
- Modify: `OctavianOS/boot/jasper/install.cfg`
- Modify: `OctavianOS/boot/jasper/recovery.cfg`
- Modify: `OctavianOS/boot/live/desktop-sessions.json`
- Modify: `OctavianOS/tests/boot/test_boot_target_graph.py`
- Modify: `OctavianOS/tests/boot/test_installer_payload_routing.py`
- Modify: corresponding `ChimeraIIOS/boot/**` files and boot tests

**Interfaces:**
- Consumes: Session IDs from `2026-11-03-desktop-sessions-voiceconnect-plan.md` and existing payload manifests.
- Produces: A resolved route graph for BIOS/UEFI × Live/Installer/Recovery with no missing configfile/module edge.

- [ ] **Step 1: Add failing route-graph cases** for every session ID, installer payload, recovery payload, and BIOS/UEFI target case.
- [ ] **Step 2: Run** `python -m pytest -q tests/boot/test_boot_target_graph.py tests/boot/test_installer_payload_routing.py` in both repositories. Expected: current 2-session and incomplete payload graph is reported.
- [ ] **Step 3: Update route and payload contracts** so every entry validates files, hashes, architecture and manifest before handoff; missing modules return to Jasper or a text fallback.
- [ ] **Step 4: Run** the focused static tests and `grub-script-check` on all tracked GRUB configs. Expected: every route resolves and no parser errors.
- [ ] **Step 5: Commit** route changes and evidence-contract updates in each OS repository.

### Task 3: Execute real Live and Recovery init in QEMU

**Files:**
- Modify: native Koronos process admission/syscall files identified by the preceding failing trace and current CPL3 probe implementation
- Modify: Live and Recovery initramfs build manifests/scripts in both repositories
- Modify: `OctavianOS/tests/qemu/README.md` and native userspace workflow
- Add: target trace fixtures under the existing `tests/migration/` directories

**Interfaces:**
- Consumes: Valid boot module list and target-specific manifests.
- Produces: Machine-readable trace with `target`, `firmware`, `init_pid`, `cpl`, `syscall_ack`, `readiness`, `desktop_id`, and process exit status.

- [ ] **Step 1: Add failing trace assertions** requiring same-PID CPL3 syscall and readiness for Live and Recovery across both firmware modes.
- [ ] **Step 2: Run** the existing QEMU acceptance workflow on the exact change. Expected: current missing-init trace remains a hard failure.
- [ ] **Step 3: Connect the actual init ELF** to selected target payload; preserve real PID attribution and provide a text recovery shell if display startup fails.
- [ ] **Step 4: Re-run** both BIOS/UEFI target cases and verify trace artifacts show the real process acknowledgement.
- [ ] **Step 5: Commit** initramfs and kernel/runtime changes only when QEMU trace assertions pass.

### Task 4: Execute and verify safe Installer workflow

**Files:**
- Modify: existing native installer source and `installation.img` composition manifest in both repositories
- Modify: `OctavianOS/boot/jasper/install.cfg` and `tests/boot/test_installer_payload_routing.py`
- Add: disposable-storage install test under existing `tests/qemu/` acceptance workflow

**Interfaces:**
- Consumes: Verified CPL3 installer process, block-device inventory, explicit chosen test target, and user-confirmed plan.
- Produces: Install result recording selected disk ID, source/target hashes, completed phases, and reboot-to-installed-system trace.

- [ ] **Step 1: Add failing QEMU cases** for no disk, multiple disks, rejected confirmation, interrupted install, successful install, and reboot to the test target.
- [ ] **Step 2: Run** the installer workflow. Expected: current production image fails its real installer-completion gate.
- [ ] **Step 3: Implement a reviewed installer UI and safe backend** that cannot write until a specific test disk and plan are confirmed; preserve recovery when a phase fails.
- [ ] **Step 4: Re-run** the disposable QEMU matrix and verify no host disk is exposed or modified.
- [ ] **Step 5: Commit** only after success/recovery traces are attached to the run.

### Task 5: Apply production acceptance and release gate

**Files:**
- Modify: `OctavianOS/docs/PRODUCTION_USERSPACE_HANDOFF.md`
- Modify: `OctavianOS/docs/NATIVE_RUNTIME_ACCEPTANCE.md`
- Modify: equivalent Chimera acceptance documents and release workflow gates
- Modify: both repository release pipelines

**Interfaces:**
- Consumes: exact-commit six-case boot traces, desktop session readiness, installer result, recovery shell readiness.
- Produces: pass/fail release report; native release publish job is enabled only after all evidence fields pass.

- [ ] **Step 1: Add failing release-gate cases** for absent/incomplete trace artifacts and wrong commit/image digest.
- [ ] **Step 2: Run** the gate on existing results. Expected: current failed handoff blocks publish.
- [ ] **Step 3: Wire exact commit and image digest** into all required evidence checks; keep release step skipped on any failure.
- [ ] **Step 4: Re-run** the native production workflow. Expected: no release is created until Live, Installer, Recovery, BIOS, and UEFI all pass.
- [ ] **Step 5: Commit and publish** native releases only on a complete pass.

