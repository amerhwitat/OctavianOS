# Production userspace handoff — acceptance and integration contract

**Handoff gate: PASS — 6/6 target/firmware cases. Production release: BLOCKED.** Latest verified six-case run: [#43412390841](https://github.com/amerhwitat/OctavianOS/actions/runs/43412390841). The native build and full-ISO QEMU boot plus full-ISO handoff verification passed in [#43412390877](https://github.com/amerhwitat/OctavianOS/actions/runs/43412390877). The corrected candidate keeps each target init resident as PID 1 and proves ordered kernel-ready → CPL3 syscall acknowledgement → user-authored readiness → kernel-verified PID1 ACTIVE markers. This verifies the persistent PID 1 handoff contract only; production VFS/root activation, service supervision, graphical Live desktop, disk-writing Installer, filesystem-repair Recovery and SMP remain unverified. Prerelease publication was skipped because this was a pull-request candidate.

## What the evidence means

The acceptance job ran the existing verifier unchanged against these traces:

- `trace/full-iso-debugcon.log` for Live
- `trace/installer-debugcon.log` for Installer
- `trace/recovery-debugcon.log` for Recovery

All six target/firmware attempts now pass the unchanged verifier with a genuine CPL3-originated syscall acknowledgement, a target-specific readiness marker carrying the same nonzero PID, and a subsequent kernel-owned persistent PID1 ACTIVE marker. The verifier remains fail-closed; do not weaken it or manufacture these markers from kernel code.

## Source-level integration gaps

The current vendored path and the upstream candidate must be treated as separate layers:

1. The selected x86_64 target ELF is now admitted, loaded into a process-owned address space and entered through the native ring-3 path in the QEMU acceptance cases. Production initramfs-to-VFS extraction and root activation remain incomplete.
2. `process.cpp` process admission is followed by verified CPL3 execution and a kernel-owned RUNNING-state PID1 marker in the current candidate. Full scheduler-managed process lifecycle and child supervision remain incomplete.
3. The native privilege transition, TSS/RSP0 setup and DPL3 INT 0x80 acknowledgement are exercised by the six passing QEMU cases; broader interrupt/device and SMP runtime coverage remains open.
4. The compatibility `syscall.cpp` dispatcher remains distinct from the native hardware syscall entry. The native path now proves process-owned GETPID, validated WRITE/readiness and persistent PID1; general EXIT/wait/reap and full Linux syscall coverage remain incomplete.
5. The full ISO QEMU run now proves the selected target init module is staged, routed and executed for Live, Installer and Recovery. This is still a small target bootstrap ELF, not a complete initramfs `/init` userspace.
6. The current full-ISO QEMU smoke plus six-case verifier proves persistent target PID1 handoff, not production service readiness or desktop/installer/recovery completion. Keep those claims separate.

Upstream [ChimeraIIOS PR #125](https://github.com/amerhwitat/ChimeraIIOS/pull/125) contains a candidate ring-3 probe path and passed its standalone acceptance workflow. It does **not** by itself prove that the real init executable is extracted from the production Live/Installer/Recovery payload and launched in the final ISO. Do not blindly copy it over OctavianOS-specific source.

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
| Live / BIOS | PASS — persistent PID 1 (candidate 2026-11-13) |
| Installer / BIOS | PASS — persistent PID 1 (dry-run only) |
| Recovery / BIOS | PASS — persistent PID 1 (diagnostics only) |
| Live / UEFI | PASS — persistent PID 1 |
| Installer / UEFI | PASS — persistent PID 1 (dry-run only) |
| Recovery / UEFI | PASS — persistent PID 1 (diagnostics only) |
| Aurora after actual Live init | NOT VERIFIED |
| Installer completion + installed boot | NOT VERIFIED |
| Recovery action | NOT VERIFIED |
| Production release | BLOCKED |

The six target/firmware handoff cases are now recorded independently and passed. The following production follow-up rows remain separate release gates.

## Completion evidence

The persistent handoff fix is verified by a successful native build, full ISO QEMU boot, six target/firmware QEMU runs, unchanged verifier PASS results and retained debug traces. The overall production release remains blocked until production payload extraction/root VFS, service startup, Aurora/compositor readiness, disposable-disk installation plus reboot, a real Recovery repair postcondition, and SMP follow-up evidence are implemented and tested.


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


## Live run refresh — 2026-10-19

A fresh GitHub Actions poll reports [upstream run #1388](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39207743325) as `in_progress`. The build job has passed boot-routing/artwork validation and the unchanged fail-closed verifier unit tests; ASM/C/C++ build and ISO composition are active. ISO validation, payload inspection, QEMU boot, production handoff checks, all six target × firmware cases, artifact upload, and release gates have not completed. No artifacts are available yet. Do not describe this as a successful build. All production runtime gates remain NOT VERIFIED and release remains BLOCKED.


## Current CI evidence refresh — 2026-10-19

Step-level polling of [ChimeraIIOS run #1388](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39207743325) confirms successful completion of: (1) ASM/C/C++ build and ISO composition, (2) ISO artifact validation, (3) target payload and offline artwork validation, and (4) headless Koronos boot smoke test. The workflow is currently in the actual Live/Installer/Recovery userspace handoff verification step. The six-case BIOS/UEFI production matrix is still pending; no trace/ISO artifacts are available yet. Do not treat build or boot smoke success as a successful production handoff. Runtime acceptance requirements remain NOT VERIFIED until their own checks pass.


## Latest status — six-case matrix in progress (2026-10-19)

Current job-step evidence for [ChimeraIIOS run #1388](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39207743325): build and ISO composition, ISO validation, target-payload/offline-artwork validation, and QEMU boot smoke all passed; actual Live/Installer/Recovery handoff verification has completed; the six-case BIOS/UEFI production matrix is now running. Its result is not yet known. No artifacts are available and release steps remain pending. Do not promote any runtime acceptance row to VERIFIED until the matrix and target-specific evidence succeed.


## Verified handoff result — 2026-10-19

[ChimeraIIOS run #1388](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39207743325) now reports successful completion of the actual Live/Installer/Recovery CPL3 init syscall + matching nonzero PID handoff check and the six-case BIOS/UEFI production userspace matrix. The target trace artifact `chimera-target-userspace-traces` is uploaded (ID 12166193261). ISO artifact upload remains in progress; GitHub Release publication and the final fail-closed gate have not completed. Mark the six-case QEMU handoff matrix PASS, but do not conflate it with process-owned CR3 teardown safety, EXIT/EXIT_GROUP lifecycle tests, Aurora startup, installer completion/reboot, operational recovery, or AP-backed concurrent SMP; those are still NOT VERIFIED.


## Corrected final verifier result — 2026-10-19

The final status of [run #1388](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39207743325) is FAILURE. The logs explicitly show `FAIL: missing user-originated init syscall acknowledgement (CPL 3), actual init PID readiness marker` for Live, Installer and Recovery under both BIOS and UEFI. The step wrappers completed but exported `accepted=false`; the final fail-closed release gate failed as intended. Therefore neither target handoff acceptance nor the six-case production matrix passed. Build/ISO and QEMU boot-smoke checks did pass, and artifacts were uploaded: `chimera-target-userspace-traces` ID 12166193261 and `chimera-ii-os-live-installer` ID 12166940637. GitHub Release publication was skipped. Keep every production runtime acceptance requirement NOT VERIFIED until real user-originated CPL3 syscall and matching PID evidence pass all cases.


## Desktop artwork update (web prototypes)

The Aurora Wayland Glass and Marine Desktop web prototypes now share an interactive wallpaper picker and bundled local artwork. Marine uses `desktop/marine/assets/marine-desktop.svg`; Aurora uses `desktop/aurora/assets/octavian-octopus-aurora.svg`. The preference is persisted in browser local storage. These UI changes do not affect or satisfy the kernel userspace acceptance gate above.


## ISO-to-production-init audit — 2026-10-19

The latest source inspection confirms why a successful ISO build still cannot satisfy the production gate:

- `vendor/chimera-ii-os/source/build-chimera-iso.sh` stages the Live and Recovery initramfs images, but the inspected ISO staging path does not build or stage a target-specific `CHIMERA_MODULE_USER_INIT_ELF`.
- `vendor/chimera-ii-os/source/kernel/core/multiboot_modules.cpp` classifies a module as `USER_INIT_ELF` from its command-line/name. Classification does not create or extract an ELF executable.
- `vendor/chimera-ii-os/source/kernel/core/target_launch.cpp` scans for exactly one bounded `USER_INIT_ELF`, then requires working address-space operations, process admission, ELF loading, a real CR3 root, and ring-3 entry. With no such module it returns without launching production init.
- The ELF admission/load-plan APIs do not prove execution, and a passing kernel/ISO smoke test does not prove a user process reached CPL 3.

No probe ELF, synthetic ready marker, or weakened verifier is an acceptable workaround. A real production init/runtime and its target-specific staging still need to be implemented and tested end to end. The current 0/6 result and release block remain unchanged.


## Fresh source scan — syscall-fix branch — 2026-10-19

Inspected branch `fix/mirror-fail-closed-process-syscalls` at candidate commit `acf56d69cb858e06c699e4735c07d622531e0287`, plus the failed verifier job from run [#39209603140](https://github.com/amerhwitat/OctavianOS/actions/runs/39209603140).

- The native kernel build, Multiboot2 module-classification tests, QEMU kernel-readiness boot, initramfs builds, ISO candidate checks, and six independent target/firmware boots completed successfully.
- The unchanged six-case matrix test harness passed its own contract tests, but each of the six production traces failed the unchanged production handoff verifier. The job log reports `FAIL: missing user-originated init syscall acknowledgement (CPL 3), actual init PID readiness marker` six times, then `PRODUCTION ACCEPTANCE FAIL: 6 of 6 cases failed or were missing`. Prerelease was skipped.
- The native live/recovery builder, `tools/build-live-boot-binaries.sh`, writes a shell-script `/init` and links BusyBox applets. This is an initramfs shell payload, not the native target-specific ELF expected by `koronos_launch_selected_userspace()`.
- The launch routine searches for exactly one `CHIMERA_MODULE_USER_INIT_ELF` and returns without launching when none is present. The audited ISO staging path does not extract/build a supported native init executable from the shell initramfs or stage a target-specific init ELF.
- `kernel/core/syscall.cpp` deliberately rejects GETPID and EXIT/EXIT_GROUP in the compatibility dispatcher when there is no active process context. The native dispatcher depends on a validated active process and real CR3/ring-3 execution; logging helpers and admission state cannot replace that execution.

This is a concrete integration/runtime blocker, not a CI retry problem. A correct fix must supply a real production-compatible native init/runtime (or implement and test the required shell/Linux ABI runtime), stage/select it separately for Live, Installer, and Recovery, and prove actual process entry and syscalls. Do not package a tiny marker-only probe, generate acceptance strings in kernel code, or weaken `tests/migration/verify-userspace-handoff.py` / `tests/migration/verify-six-case-userspace-matrix.py`.

**Historical snapshot:** this earlier scan recorded 0/6 production target/firmware cases. The candidate probe and integrated build results below supersede its source/build snapshot; production acceptance remains a separate gate.


## Chimera six-case candidate import — 2026-10-19

OctavianOS PR [#81](https://github.com/amerhwitat/OctavianOS/pull/81) was merged as [commit 1aba005](https://github.com/amerhwitat/OctavianOS/commit/1aba0058f2b62c362e1812eaadb22aad8fea5964). It imports the upstream ChimeraIIOS ring-3 candidate at [source commit 506c76b](https://github.com/amerhwitat/ChimeraIIOS/commit/506c76baafcc45fc08dd14fad5b1723f2d0fd24b) into the vendored Koronos source and adds a Live/Installer/Recovery × BIOS/UEFI probe workflow.

**Candidate probe status: PASS 6/6.** OctavianOS [acceptance run #39229471886](https://github.com/amerhwitat/OctavianOS/actions/runs/39229471886) passed all six standalone ELF probe cases and the BIOS timeout checks. The integrated [native build run #39229471842](https://github.com/amerhwitat/OctavianOS/actions/runs/39229471842) built the native ISO candidate and passed kernel boot readiness plus Installer/Recovery routing smoke checks.

**Production acceptance: FAIL / release blocked.** The same native build run's unchanged production verifier failed for Live, Installer, and Recovery because the final production ISO traces still lack the user-originated CPL3 init syscall acknowledgement and matching actual init PID readiness marker. The prerelease job was skipped. The standalone probes are not the actual production shell-based initramfs payload.

Remaining independent gates: stage/select and execute the actual target-specific production init, prove Live init → Aurora, complete installation and reboot to the installed system, perform a real Recovery action, and demonstrate AP-backed concurrent SMP. Keep tests/migration/verify-userspace-handoff.py fail-closed; never synthesize readiness markers or publish a production release before those gates pass.

## Linux kernel-to-userspace reference and persistent PID 1 fix — 2026-11-13

Linux is used as a behavioral reference, not as code to copy blindly. The relevant Linux boot contract is:

1. The bootloader passes the kernel its boot parameters and initramfs.
2. The kernel unpacks initramfs into the initial root filesystem and prepares the root namespace.
3. The kernel locates and executes the selected init program (normally /init from initramfs, or a configured init path).
4. PID 1 remains alive as the first userspace process, mounts/activates required filesystems, starts and supervises services, and coordinates the transition from early userspace to the real root where applicable.
5. The system is not considered userspace-ready merely because the kernel entered an ELF or a one-shot program printed a banner and exited.

Koronos target equivalent and current implementation boundary:

| Linux reference phase | Koronos target phase | Current status |
|---|---|---|
| Boot parameters + initramfs handoff | Multiboot2 target module + target=live/installer/recovery | Module classification and target identity checks exist |
| Unpack initramfs into rootfs/VFS | Bounded CPIO extraction, VFS publication, mount /, /dev, /proc, writable /tmp | NOT IMPLEMENTED / NOT VERIFIED |
| Execute selected /init as PID 1 | Validate exact target ELF, create address space, load ELF, enter CPL3 | Native x86_64 path exists; production rootfs-to-init binding still incomplete |
| PID 1 service bootstrap | Kernel confirms the same process remains RUNNING after its user-originated readiness write | Candidate fix on this branch: target inits stay resident; kernel disarms the startup deadline only after validating readiness and process state, then emits the kernel-owned PID1-active record |
| Service supervision / restart / wait | Kore service manager, process wait/reap, restart policy, health checks | NOT IMPLEMENTED / NOT VERIFIED |
| Live session startup | PID 1 starts display server/compositor, input and selected desktop | Text console probe only; no native compositor/X server |
| Installer | PID 1 starts storage discovery, partition/filesystem operations, install, bootloader setup and reboot verification | Dry-run only; no block-device writer |
| Recovery | PID 1 starts filesystem checks/repair and validates postconditions | Diagnostics only; no repair backend |

### Candidate handoff correction

The latest failed native build [run #43409174831](https://github.com/amerhwitat/OctavianOS/actions/runs/43409174831) produced the three target readiness markers but no kernel-verified persistent PID 1 active marker. The underlying defect was concrete: each target init called init_exit(0) after printing readiness, and koronos_launch_selected_userspace() then reclaimed its address space. A clean exit was being mistaken for a running PID 1.

The candidate branch now changes this lifecycle:
- Live, Installer and Recovery call a shared non-returning init_pid1_wait() after readiness instead of exiting.
- The kernel checks that the same admitted PID is still CHIMERA_PROCESS_RUNNING when its validated user write contains the target/PID readiness line.
- Only after that check does the kernel disarm the startup-only PIT deadline and emit KORONOS PID1 ACTIVE with the same PID.
- The verifier remains fail-closed; it still rejects absent/mismatched active markers and any subsequent process-exit/timeout evidence.
- Source-contract unit tests cover all three target init binaries and the kernel-owned active-marker gate.

This corrects the immediate one-shot-probe-versus-PID1 lifecycle mismatch. It does not yet provide a complete initramfs VFS, service manager, graphical Live session, disk-writing installer or filesystem repair implementation. The candidate must pass a fresh native build and all six BIOS/UEFI target cases before it can be called verified.

### Linux source references

Use the Linux kernel source as the semantic reference for the lifecycle above:
- init/initramfs.c and init/do_mounts_initrd.c: initramfs unpacking and early root preparation.
- init/main.c: kernel initialization and transition to userspace init.
- kernel/fork.c, kernel/exit.c, kernel/pid.c: process creation, PID lifecycle and exit semantics.
- fs/ and fs/proc/: VFS, filesystems and process observability.
- kernel/sched/: runnable task lifecycle, scheduling and wait/wakeup behavior.

For Koronos, implement equivalent contracts behind Koronos-owned APIs and architecture code. Do not claim Linux ABI or full Linux userspace compatibility until the corresponding syscalls, VFS, process model and userspace runtime are implemented and tested.
