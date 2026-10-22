# Production userspace handoff — acceptance and integration contract

## Root cause found in the current production path — 2026-10-22

The latest trace-verifier job (run [39728253993](https://github.com/amerhwitat/OctavianOS/actions/runs/39728253993), job [119659006555](https://github.com/amerhwitat/OctavianOS/actions/runs/39728253993/job/119659006555)) reports all three targets missing both the CPL3-originated init syscall acknowledgement and PID-bound readiness marker.

Source inspection identifies the concrete integration break:

- The production ISO workflow stages the Live/Recovery initramfs or Installer image plus manifests/contracts as Multiboot2 modules. Its target-specific GRUB configuration does not stage a chimera-user-init-elf / user-init.elf module.
- multiboot_modules.cpp can classify such a module if present, but classification does not create one.
- target_launch.cpp only enters ring 3 after finding exactly one CHIMERA_MODULE_USER_INIT_ELF. The Live initramfs built by tools/build-live-boot-binaries.sh contains a /init shell script and BusyBox links, i.e. a Linux-style initramfs; Koronos's native ELF launcher does not interpret shell scripts or provide the Linux syscall/runtime environment needed to execute that BusyBox binary.
- Consequently, the production boot path can recognize the target payload and still never enter the native user process. The candidate-probe matrix passes because it supplies a purpose-built probe ELF; it is a different input path and is not production evidence.

This is a missing executable/runtime integration, not a verifier-format issue. Do not add a marker-only shim or reuse the candidate probe as production init. The real fix requires a native target init ELF/runtime that is actually built from production sources, staged by the production ISO builder with an unambiguous target tag, launched by Koronos, and connected to the target's actual initramfs/services. The current commit adds an explicit fail-closed error and ensures production payload boots reach that check; it improves diagnosis but does not claim that the native runtime has been implemented.

**Status: BLOCKED — 0/6 production target/firmware cases passed.** Latest verified run: [OctavianOS Actions run 39209603140](https://github.com/amerhwitat/OctavianOS/actions/runs/39209603140). Koronos build and ISO-candidate checks passed, but Live, Installer, and Recovery × BIOS/UEFI all failed the unchanged production verifier because the traces lack a genuine CPL3-originated init syscall acknowledgement and a matching nonzero kernel-owned PID readiness marker. Production prerelease was skipped. Passing routing-contract and source-integration checks are not userspace acceptance.

## Latest independent evidence — 2026-10-22

The target-specific candidate/probe workflow run [39728253938](https://github.com/amerhwitat/OctavianOS/actions/runs/39728253938) reports successful BIOS/UEFI boot-probe jobs for Live, Installer, and Recovery. These jobs validate the target-specific probe and boot path; they do **not** establish that the final production initramfs launches the real init process.

The separate production trace verifier run [OctavianOS run 39728253993](https://github.com/amerhwitat/OctavianOS/actions/runs/39728253993) downloaded the full-ISO traces and failed for all three production targets with the missing user-originated init syscall acknowledgement (CPL 3) and actual init PID readiness marker. Its prerelease step was skipped. Therefore the current evidence is **6/6 candidate probe jobs successful, but production init handoff still FAILS**; storage persistence, service supervision, Aurora handoff, installer write/verify/reboot, recovery repair, and AP-backed SMP remain independently unproven.

Do not convert the candidate-probe successes into production acceptance or weaken the verifier. Re-run the unchanged production verifier after fixing the real initramfs → ELF loader → ring-3 syscall → PID-bound readiness path.

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

## Native init artifact and production GRUB integration — 2026-10-22

A dedicated freestanding native init has now been added under `vendor/chimera-ii-os/source/kernel/userspace/native_init.c`, with an explicit ELF layout in `native_init_linker.ld`. The kernel build compiles three target-specific ELFs (`native-init-live.elf`, `native-init-installer.elf`, and `native-init-recovery.elf`) from this source; it does not rename or copy the candidate `user_init_smoke.c` probes. Build checks require ELF64 ET_EXEC and distinct RX plus RW PT_LOAD segments.

The production ISO layout stages these artifacts under `/boot/koronos/`, and the main GRUB and Jasper Live/Installer/Recovery entries pass the matching ELF as `chimera-user-init-elf target=<target>`, separately from the initramfs or installation data module. The six-case acceptance workflow now stages and boots the dedicated native init against the selected production payload rather than using the probe ELF as its production init.

The native init issues `INT 0x80` for the CPL3-gate acknowledgement, obtains its PID through `CHM_SYS_GETPID`, and invokes `CHM_SYS_VALIDATE_BOOT_PAYLOAD` before emitting readiness. The kernel validates a gzip envelope for the selected Live/Recovery initramfs or checks the Installer image plus required JSON contract modules. The init then writes the target/PID-bound readiness token through `CHM_SYS_WRITE`, checks the write result, and exits through the native ABI. The existing verifier remains unchanged. This establishes a real process/syscall handoff only if all six QEMU cases pass; source wiring alone is not proof.

**Explicit scope boundary:** the current native init does not claim that a VFS has been mounted, that the CPIO/initramfs contents are accessible through a filesystem API, that storage persists across reboot, that services are supervised, or that Aurora/Installer/Recovery workflows are complete. Those remain separate release gates. Do not label the OS production-ready based only on this minimal native-init handshake.


## Fresh production acceptance audit — 2026-10-22

Current head acceptance run [39736291623](https://github.com/amerhwitat/OctavianOS/actions/runs/39736291623) was checked directly. All six jobs are queued: Live × BIOS/UEFI, Installer × BIOS/UEFI, Recovery × BIOS/UEFI. A queued job is neither a pass nor a failure; do not infer a result from previous commits. Native desktop component compile run [39736291844](https://github.com/amerhwitat/OctavianOS/actions/runs/39736291844) completed successfully, while desktop contract run [39736291681](https://github.com/amerhwitat/OctavianOS/actions/runs/39736291681) had started. Neither proves the remaining runtime acceptance gates.

### Confirmed source-level blockers beyond the native-init handshake

- **Filesystem and durable storage:** target payload validation checks module presence and a limited envelope/JSON prefix. It does not mount an initramfs or filesystem, perform file operations, flush durable data, or prove write/read persistence across a reboot. ISO extraction and hashes prove artifact integrity only.
- **Installer:** no fresh end-to-end evidence proves the installer writes a target disk, verifies the installed image, reboots, and boots the installed system.
- **Recovery:** no fresh end-to-end evidence proves a recovery operation changes/repairs a target and validates the result.
- **Aurora:** the minimal native init's PID/syscall/readiness handshake is not an Aurora session handoff. The production path still needs actual userspace service startup and a verifiable session/display handoff.
- **SMP:** `kernel/core/parallel.cpp` deliberately returns zero when more than one worker is requested, and `kernel/core/scheduler.cpp::chimera_sched_run_parallel()` currently returns zero unconditionally. This fail-closed behavior is honest but confirms that AP-backed concurrent worker dispatch is not implemented. Do not weaken the guard or report sequential callback execution as SMP.
- **Desktop providers/preferences:** compile and schema/contract checks do not prove native preference persistence or working input, audio, display, and service providers. These require runtime tests against the real backends.

### Required closeout evidence

1. Capture all six production ISO traces and verify each has a CPL3-originated syscall acknowledgement, a nonzero kernel-owned PID, and a matching target/PID readiness marker.
2. Add end-to-end filesystem and storage tests, including write, flush, reboot, and read-back from the same virtual disk.
3. Exercise a real install → reboot → installed-system boot path and a real recovery repair path.
4. Prove initramfs/rootfs mount and service supervision, then verify Aurora is actually entered.
5. Run preferences and device/service tests against functional native providers, including persistence after process/application restart.
6. Boot APs independently and prove simultaneous per-CPU work using synchronized overlap evidence and cross-core correctness tests.

Until those artifacts exist, this PR remains draft and production publication remains blocked. Keep the verifier fail-closed; do not fabricate readiness or substitute probe-only evidence for production workflows.


## Cross-edition propagation: Mobile edition and ISO/Flash tool — 2026-10-22

This section records the required propagation boundary across OctavianOS desktop, Mobile edition, the matching ChimeraIIOS implementation, and the public ISO/Flash Center. It is an integration contract, not a claim that the items below are already complete.

- **Shared source of truth:** keep the boot-target ABI, native-init artifact names, target IDs, module aliases, manifest schema, and acceptance marker format synchronized between OctavianOS and ChimeraIIOS. Mobile must consume the same versioned contracts while selecting mobile-specific drivers/compositor and architecture-appropriate boot assets; it must not advertise x86_64 ISO support as ARM64/mobile boot support.
- **Mobile edition gate:** build and test Mobile independently for each declared architecture/device profile. Verify boot route, input/touch, display, audio, storage, settings persistence, service supervision, and Aurora/Marine session routing on supported hardware or an explicitly labeled emulator. Unsupported providers must be shown as unavailable rather than silently mapped to desktop implementations. Mobile builds do not count as evidence for the six BIOS/UEFI ISO cases or AP-backed SMP.
- **ISO/Flash Center gate:** the web UI may inspect ISO metadata and checksums without elevated privileges. Destructive writes must remain behind explicit confirmation (CHIMERA_FLASH_CONFIRM=YES), require a validated image and an explicitly selected /dev/... target, reject arbitrary shell commands and ambiguous targets, and verify the written image afterward. Device detection and image verification are not proof of a successful boot or installed-system handoff. Do not trigger physical flashing from CI or automatically on page load.
- **Cross-project parity:** changes to native-init names, boot manifests, target routing, flash API contracts, or acceptance evidence must be reflected in both OS repositories and the public site in one coordinated change set; link the corresponding commits and keep each project’s status independent. Avoid claiming parity based on a copied file or a green contract-only job.
- **Current evidence boundary:** OctavianOS native desktop component compilation previously passed, but the six production Live/Installer/Recovery × BIOS/UEFI jobs were still queued at the last check. ChimeraIIOS has native-init build artifacts but lacks the matching ring-3 launch backend on this branch. Neither result establishes production userspace readiness, VFS mount/file operations, durable storage, Installer/Recovery workflows, Aurora handoff, or genuine AP concurrency.

### Cross-edition closeout checklist

- [ ] Mobile architecture/device matrix builds and runtime checks pass; unsupported targets are explicit.
- [ ] Flash Center API and UI contract tests pass, including invalid-image, wrong-target, cancellation, and post-write verification failures.
- [ ] The same ABI/manifest/target routing is verified against both OS repositories and site metadata.
- [ ] All six production ISO cases produce real CPL3 syscall acknowledgements and PID-bound target readiness.
- [ ] Live initramfs is mounted and file operations are exercised; Installer writes persist across reboot; Recovery performs and verifies a real repair.
- [ ] Aurora session handoff, settings persistence, real input/audio/display providers, and AP-backed parallel execution are demonstrated.
- [ ] Publication remains blocked until relevant release gates pass; contract checks and candidate probes are not substitutes for production evidence.
