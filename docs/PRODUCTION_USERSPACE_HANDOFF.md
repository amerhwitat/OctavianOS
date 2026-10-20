# Production userspace handoff — acceptance and integration contract

**Status: BLOCKED — 0/6 production target/firmware cases passed.** Latest verified run: [OctavianOS Actions run 39406419376](https://github.com/amerhwitat/OctavianOS/actions/runs/39406419376) (2026-10-20). The native Koronos build and ISO candidate, ELF/Multiboot2 checks, module-classification tests, syscall ABI regression guard, QEMU kernel/ISO boot-to-Koronos checks, and process page-table self-test passed. The separate production verifier job failed for Live, Installer, and Recovery: all three traces lack the required user-originated CPL3 init syscall acknowledgement and matching nonzero kernel-owned PID readiness marker. Installer and Recovery logs explicitly say handoff is withheld because no supported production init ELF/runtime is wired to the payloads. The prerelease job was skipped. This is a successful kernel/ISO smoke build, not production userspace acceptance.

## What the evidence means

The acceptance job ran the existing verifier unchanged against these traces:

- `trace/full-iso-debugcon.log` for Live
- `trace/installer-debugcon.log` for Installer
- `trace/recovery-debugcon.log` for Recovery

All six target/firmware attempts failed because they lack both a user-originated init syscall acknowledgement proving CPL 3 and a subsequent target-specific readiness marker carrying the same real, nonzero init PID. The verifier is intentionally fail-closed; do not weaken it or manufacture these markers from kernel code.

## Source-level integration gaps

The current vendored path and the upstream candidate must be treated as separate layers:

1. `process_loader.cpp` validates ELF load segments and maps/initializes memory through callbacks; this alone does not schedule or enter the image.
2. `process.cpp` records ELF metadata/PID admission. Admission is not proof that an instruction executed in ring 3.
3. `interrupt.cpp` installs DPL-0 IDT gates and explicitly defers ring-3 exposure until TSS, stack, and address-space setup are complete.
4. The compatibility `syscall.cpp` dispatcher is not itself a hardware syscall entry/return path; its current GETPID/EXIT semantics are insufficient evidence of process-owned PID and teardown.
5. Multiboot module classification recognizes a possible `CHIMERA_MODULE_USER_INIT_ELF`, but classification is not proof that the ISO build actually stages the target's production init ELF or that the launch path selects it.
6. The current QEMU smoke gates prove kernel readiness and target routing only. They must not be renamed or documented as production userspace acceptance.

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
| Live / BIOS | NOT VERIFIED — current aggregate Live trace fails |
| Installer / BIOS | NOT VERIFIED — current Installer trace fails |
| Recovery / BIOS | NOT VERIFIED — current Recovery trace fails |
| Live / UEFI | NOT VERIFIED |
| Installer / UEFI | NOT VERIFIED |
| Recovery / UEFI | NOT VERIFIED |
| Aurora after actual Live init | NOT VERIFIED |
| Installer completion + installed boot | NOT VERIFIED |
| Recovery action | NOT VERIFIED |
| Production release | BLOCKED |

The existing aggregate run demonstrates that all three target traces fail; it does not establish six independent BIOS/UEFI outcomes. Record each case separately once the workflow runs them separately.

## Completion evidence

A source change is not complete until CI demonstrates: successful native build; ELF/module contract tests; production payload extraction tests; six target/firmware QEMU runs; verifier PASS for every trace without modifying the verifier; preserved debug traces; and Aurora/installer/recovery follow-up evidence. Until then, report the gate as BLOCKED rather than inferring success from a kernel-ready marker.


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


## Current verification refresh — 2026-10-20 (run #39404402300)

**Release decision remains BLOCKED.** The native Koronos build job passed, but the unchanged production verifier failed for Live, Installer, and Recovery. The verifier reported missing user-originated init syscall acknowledgement (CPL 3) and actual init PID readiness evidence in each of the three aggregate traces. The prerelease job was skipped. See [run #39404402300](https://github.com/amerhwitat/OctavianOS/actions/runs/39404402300).

The separate [ring-3 probe matrix #39404402308](https://github.com/amerhwitat/OctavianOS/actions/runs/39404402308) passed all six probe jobs (Live/Installer/Recovery × BIOS/UEFI), but the workflow explicitly labels them **not production acceptance**. Passing those probes does not establish that production init ELFs are staged in the ISO or that target services start.

The ordered kernel handshake has been hardened on branch `fix/native-init-elf-contract-guard-20261020`: a verified CPL3 syscall acknowledgement must precede a target/PID diagnostic matching the kernel-owned PID, and only then can a matching target readiness line be recognized. The ring-3 smoke payload now exercises that order. This is a contract/probe change only; it is not a service implementation and must not be used to relabel the probe payload as production init.

The key unresolved integration failure is still end-to-end production execution: the actual production payload path must stage and select a real target init ELF, enter it at CPL3, and let it initialize target services before it emits readiness. VFS/filesystem/device services, Aurora handoff, installer transaction/reboot, recovery repair, and AP-backed SMP remain NOT VERIFIED. Keep `tests/migration/verify-userspace-handoff.py` unchanged. Do not synthesize acknowledgements, PIDs, or readiness; keep prerelease publication gated on real production verifier passes and follow-up functional acceptance.


## Linux-inspired target-init proposal audit — 2026-10-20

**Decision: do not promote the proposed `target_init.c` sample to production or stage it as a production init.** The architectural direction (one PID-1-style target supervisor with target-specific service startup and readiness only after success) is sound, but the supplied implementation currently reports success without initializing those services.

Concrete ABI/source findings on branch `fix/native-init-elf-contract-guard-20261020`:

- `kernel/core/syscall.cpp` implements the process-bound native syscall path for GETPID, WRITE, EXIT and a few basic operations. FORK/EXECVE/WAITPID return ENOSYS; there is no implemented mount syscall or device-control syscall in the native dispatcher. The compatibility dispatcher intentionally rejects GETPID and EXIT without process context.
- Therefore the proposed `CHM_SYS_MOUNT=10` and `CHM_SYS_DEVCTL=11` are placeholders, not supported ABI calls. Calling them and returning success locally would not mount `/proc`, `/sys`, or `/dev`, initialize a device manager, launch Aurora, run an installer transaction, or repair a system.
- The sample's `init_virtual_filesystems()`, `init_device_subsystem()`, and `execute_target_payload()` return zero unconditionally. Its `sleep(5)` and hosted headers also assume a libc/POSIX runtime that the freestanding native-init build does not currently provide.
- The production ISO build does not currently extract and stage a native production init ELF from each shell-based initramfs. The current `build-koronos.sh` outputs `user-init-live/installer/recovery.elf` from `kernel/tests/user_init_smoke.c`; the source and comments correctly designate these as probes. Reusing those artifacts as production init would only turn a probe into a mislabeled probe.
- The kernel launch path calls the user image and then expects it to return after readiness. A real PID-1 supervisor must remain alive, which requires a safe scheduler/process lifecycle and a defined post-readiness handoff; an infinite loop cannot simply be dropped into the current one-shot launch path without proving timer/interrupt behavior, process ownership, and control flow.

The latest integrated native build [run #39405093270](https://github.com/amerhwitat/OctavianOS/actions/runs/39405093270) confirms the kernel/ISO candidate job passes, while the unchanged production verifier fails Live, Installer, and Recovery with missing CPL3-origin acknowledgement and matching actual-PID readiness evidence. The six-case probe matrix [run #39405093493](https://github.com/amerhwitat/OctavianOS/actions/runs/39405093493) passed as a probe workflow only; it is explicitly not production acceptance.

### Required implementation order

1. Define and implement a real kernel ABI for the operations actually needed (or a native service IPC/capability interface). Do not reserve syscall numbers by assumption; document and test dispatch, argument validation, user-memory access, errors, and process identity.
2. Implement real target service backends and observable success/failure results: VFS/rootfs and required mounts, device enumeration/console/input/display, and service lifecycle. Until a backend exists, init must fail closed and must not print readiness.
3. Build a freestanding native init against the supported ABI (not hosted `unistd.h`/libc assumptions); include target-specific service plans, bounded startup, diagnostic error codes, and a supervisor lifecycle compatible with the kernel scheduler.
4. Extract or build the real target init for each Live/Installer/Recovery payload, validate archive paths and ELF bounds, stage it as exactly one target-matched `CHIMERA_MODULE_USER_INIT_ELF`, and verify the final ISO contents.
5. Add host-side tests for target selection, missing/duplicate modules, unsupported syscall errors, startup failure, PID formatting/overflow, and readiness ordering. Keep `tests/migration/verify-userspace-handoff.py` unchanged.
6. Prove six actual production boots, then separately verify Live-to-Aurora, installer disk transaction/reboot, a real recovery operation, and AP-backed concurrent SMP. Release remains blocked until all required gates pass.

**Current result:** no production-init implementation or new boot success is claimed by this audit. The proposal is retained as an architecture direction, not accepted as working code. Release stays BLOCKED; no prerelease should be published.


## Native init patch review and ABI regression guard — 2026-10-20

The proposed code was not copied verbatim because its syscall assumptions conflict with the current ABI. In `kernel/include/chimera/syscall.h`, IDs 10, 11, and 12 are already `CHM_SYS_MMAP`, `CHM_SYS_MUNMAP`, and `CHM_SYS_IOCTL`. Adding mount=10/devctl=11 would alias existing memory-management calls; it is not a safe extension. The current process-bound dispatcher also has no implemented VFS mount or device-control operation, so returning success or inventing readiness would be incorrect.

### Code change made

- Added `vendor/chimera-ii-os/source/tools/tests/test_native_init_syscall_abi.py`. It asserts the complete existing native syscall ID table, checks that unsupported mount/devctl names are not introduced as aliases, and verifies that the current GETPID/WRITE dispatch contract remains present.
- Integrated this regression test into `kernel/build-koronos.sh` before native kernel compilation, alongside the existing ELF validator test.
- Commits: `5d839e71ee0076a34ea82c8a028e84463132c7d5` (test) and `c7a01eec1e9ed2e8f2b402cb8c737c5f391e5776` (build integration).

This is a preventive ABI-hardening change; it is not a production userspace implementation. The build script continues to label `user-init-live/installer/recovery.elf` as probes. No initramfs or ISO staging was switched to a nonfunctional binary. A real mount/device service API, VFS/filesystem implementation, service lifecycle, and post-readiness supervisor are still missing or unverified. The current yield syscall is explicitly a safe no-op in the bootstrap single-process path, so a tight forever-yield loop would not yet provide sleeping or CPU-efficient supervision.

### Acceptance status

The existing production verifier remains unchanged and fail-closed. The earlier latest verified native candidate run `39405093270` failed the aggregate Live/Installer/Recovery traces; probe matrix `39405093493` passed only as probes. The newly added source commits must receive CI runs before the regression test itself can be marked PASS. Production acceptance remains NOT VERIFIED and release remains BLOCKED.
