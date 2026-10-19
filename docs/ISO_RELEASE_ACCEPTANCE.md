# OctavianOS ISO release acceptance

This checklist is fail-closed: source validation and a kernel-entry marker do not establish production readiness.

## Required evidence before publishing a release candidate

- [ ] Canonical ISO build completes and checksum verification passes.
- [ ] Extracted ISO contains the x86_64 Koronos ELF, GRUB/Jasper target configs, Live and Recovery initramfs/manifests, dedicated Installer payload/contracts, and all required offline artwork.
- [ ] QEMU Live boot records a **userspace-originated** init marker, user I/O, target-ready marker, and `AURORA READY` from the actual desktop/session path.
- [ ] Installer QEMU boot reaches installer userspace and exercises a safe, disposable virtual-disk installation; the installed virtual disk reboots and reaches the same readiness contract.
- [ ] Recovery QEMU boot reaches its dedicated recovery userspace and exposes working diagnostic commands.
- [ ] SMP acceptance proves at least two logical CPUs online and concurrent execution with per-CPU evidence; `-smp 2` by itself is not proof.
- [ ] BIOS and UEFI cases pass for every supported target. Unsupported architectures must fail closed rather than reuse an x86_64 payload.
- [ ] Boot art is present inside the ISO and can be rendered offline. SVG source files do not count as GRUB-renderable art until a PNG/JPEG derivative is generated, embedded, and checked in the ISO.

## Reporting rules

- Documented is not implemented; cataloged is not executable; compiled is not booted; booted is not userspace-ready.
- A GRUB menu entry, module staging message, kernel-ready marker, or scheduler-loop marker is not target acceptance.
- Keep release publication disabled until the full checklist is backed by real build artifacts and QEMU logs. Do not override this policy merely to produce a release.

## Current status

The original Octopus Aurora SVG source and manifest are tracked in `desktop/aurora/assets/`. GRUB-stage rasterization and embedding of that artwork remain unverified by this source asset alone. Production Live/Aurora, Installer install/reboot, Recovery, installed-disk boot, and genuine SMP acceptance remain separate gates until real QEMU evidence is attached.


## Firmware-stage artwork rendering

The Octopus/Aurora SVG is the editable source artwork. Render a GRUB-friendly raster derivative with:

```sh
sudo apt-get install python3-cairosvg
python3 tools/boot/render_boot_artwork.py --output build/boot-artwork/octavian-octopus-aurora.png
```

The `OctavianOS Boot Artwork` workflow validates the PNG signature and dimensions and uploads the generated file as a workflow artifact. This is only the rasterization step: a release builder must still copy the PNG to its boot-stage path, reference that path from the Jasper/GRUB configuration, and verify it exists in the extracted ISO. A workflow artifact or desktop SVG is not proof of ISO inclusion.


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


## Live workflow status refresh — 2026-10-19

Upstream full-ISO run [#1388](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39207743325) currently reports `in_progress`. Routing/artwork validation and fail-closed verifier unit tests passed; the ASM/C/C++ build and ISO composition step remains active. Subsequent ISO integrity/payload checks, QEMU, target-specific userspace handoff, six-case BIOS/UEFI matrix, trace/ISO artifacts, and release steps remain pending. The artifacts endpoint currently returns none. This status is not a pass: production acceptance is NOT VERIFIED and release is BLOCKED until real evidence clears the unchanged gate.


## Current ISO gate progress — 2026-10-19

[Run #1388](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39207743325) has completed the ASM/C/C++ build and ISO composition, ISO artifact validation, target payload/offline artwork validation, and headless Koronos QEMU boot smoke test successfully. Actual Live, Installer, and Recovery userspace handoff verification is currently in progress. The six-case BIOS/UEFI matrix, trace and ISO artifact upload, and validated release publication have not run yet; the artifacts endpoint is empty. This is not a production release pass. Keep release BLOCKED until the unchanged fail-closed acceptance gate passes.


## Latest gate status — 2026-10-19

The upstream [run #1388](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39207743325) has passed build/ISO composition, ISO artifact validation, target payload/offline artwork validation, headless Koronos boot smoke, and the actual Live/Installer/Recovery handoff verification step. The six-case BIOS/UEFI production userspace matrix is now in progress. Trace upload, ISO artifact publication, validated release publication, and the final fail-closed release gate remain pending. No artifacts exist yet; release remains BLOCKED pending results.


## Six-case gate result — 2026-10-19

The six-case BIOS/UEFI userspace matrix and target handoff verification steps in [run #1388](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39207743325) have completed successfully. The `chimera-target-userspace-traces` artifact is uploaded (ID 12166193261). ISO artifact upload is in progress; validated release publication and the final fail-closed acceptance step remain pending. This is a pass for the defined QEMU CPL3 init syscall + matching nonzero PID handoff gate, not proof of every OS-level production requirement. Keep process cleanup, Aurora startup, install/reboot, recovery operation and AP-backed SMP unverified unless their independent evidence exists.


## Final result correction — 2026-10-19

[Run #1388](https://github.com/amerhwitat/ChimeraIIOS/actions/runs/39207743325) ended with FAILURE at the final fail-closed acceptance gate. All six target × firmware traces report missing user-originated CPL3 init syscall acknowledgement and matching actual init PID readiness. Build/ISO composition, ISO validation, payload/artwork validation, Koronos boot smoke, ISO compression, and artifact uploads passed. The release publication step was skipped. Preserved artifacts: ISO ID 12166940637; target traces ID 12166193261. The intermediate matrix step reported a successful *step conclusion* while exporting `accepted=false`; do not interpret that as matrix pass. Production acceptance is NOT VERIFIED and release remains BLOCKED.


## Status refresh — 2026-10-19 (run 39271192234)

**Release remains BLOCKED.** [Six ring-3 smoke probes](https://github.com/amerhwitat/OctavianOS/actions/runs/39271188845) passed as test-only probes. [Native build #39271192234](https://github.com/amerhwitat/OctavianOS/actions/runs/39271192234) built the kernel and support payloads but failed production-init validation because the Live, Installer and Recovery init ELF files were absent. The full-ISO boot/routing checks and real-userspace acceptance jobs were skipped. No ISO artifact was produced; only the kernel ELF artifact was uploaded.

| Gate | Current status |
|---|---|
| ELF loader hardening/regressions | Implemented; smoke CI passed |
| Six ring-3 smoke probes | PASS — test-only, not production acceptance |
| Production Live init ELF | MISSING |
| Production Installer init ELF | MISSING |
| Production Recovery init ELF | MISSING |
| Live init → Aurora | NOT VERIFIED |
| Real install → reboot → installed boot | NOT VERIFIED |
| Real Recovery operation | NOT VERIFIED |
| AP-backed concurrent SMP | NOT VERIFIED |
| Production ISO release | BLOCKED |

Do not relax the validator or substitute smoke probes. The next required implementation is the real process execution/syscall lifecycle (address-space activation, GDT/TSS/RSP0, CPL3 entry/return, validated syscall ABI and kernel-owned PID/lifecycle), followed by target-specific service/init payloads and the full six-case ISO matrix plus independent end-to-end and SMP tests.

## Runtime parity update — 2026-10-19

The ring-3 launch foundation exercised by OctavianOS smoke probes has been synchronized to ChimeraIIOS source. Chimera's own six-case smoke workflow was added and is currently pending CI. This improves code parity but does not create production target services.

| Gate | Current result |
|---|---|
| OctavianOS six ring-3 smoke probes | PASS — test-only, run #39272210956 |
| ChimeraIIOS source-parity smoke matrix | PASS — six test-only probes, run #39274699829; production acceptance separate |
| Production Live/Installer/Recovery init ELFs | MISSING |
| Full-ISO Live/Installer/Recovery × BIOS/UEFI | NOT VERIFIED |
| Aurora startup, installation/reboot, real recovery | NOT VERIFIED |
| AP-backed concurrent SMP | NOT VERIFIED |
| Production ISO release | BLOCKED |

The production release workflow remains fail-closed. Never substitute smoke-probe ELFs for the three production init payloads.

CI update: ChimeraIIOS native Koronos build #39274513564 now PASSes after the runtime parity sync. The Chimera six-case smoke workflow #39274699829 completed successfully across all six test-only probes; source-level runtime parity is now smoke-tested. Production target init ELFs remain missing. Production target init ELFs remain missing; full-ISO production acceptance and release are still BLOCKED.

Latest release-gate evidence: native run #39274902857 again passed kernel/QEMU readiness and generated Live/Recovery initramfs payloads, but failed closed because all three production init ELFs remain missing. Full-ISO checks and prerelease were skipped. A newer native run #39275375884 is pending; production ISO publication remains BLOCKED.


## Production-init ELF root cause — 2026-10-19 (run #39275559014)

[Latest native ISO run #39275559014](https://github.com/amerhwitat/OctavianOS/actions/runs/39275559014) failed at the production init ELF validator. The builder has no compile/stage rule before validation, and the shipping GRUB Live/Normal/Recovery/Installer entries do not pass a target-specific `chimera-user-init-elf` module. The current syscall ABI also lacks the filesystem/process/device/graphics services needed to turn the shell initramfs payloads into an actual Aurora, installer, or recovery session. These are implementation gaps, not missing files that can safely be filled with smoke binaries.

| Gate | Verified status |
|---|---|
| Kernel build + kernel QEMU readiness | PASS |
| Ring-3 smoke probes (six target/firmware combinations) | PASS — test-only |
| Production init ELF source/build/staging/routing | MISSING |
| Full ISO build and full-ISO target verification | SKIPPED after fail-closed payload check |
| Live→Aurora | NOT VERIFIED |
| Installer → safe disk install → reboot → installed boot | NOT VERIFIED |
| Recovery action | NOT VERIFIED |
| AP-backed concurrent SMP | NOT VERIFIED |
| Production release | BLOCKED |

Do not bypass the validator, promote smoke probes, or accept a marker-only init as production. Resume release work only after implementing the native userspace service contract and real target init programs, wiring them into the ISO and GRUB modules, and proving each target under both BIOS and UEFI. Keep release publication gated on the resulting runtime traces and operation-specific tests.


## Native init ELF build and routing integration — 2026-10-19

A freestanding target-specific ELF build/staging step is now wired into `boot/iso/build-iso.sh`; the three target payload paths are populated from a shared source compiled with distinct Live, Installer, and Recovery identities. Main GRUB and Jasper entries pass the appropriate ELF as `chimera-user-init-elf target=live|installer|recovery`.

These are explicitly **fail-closed bootstrap ELFs**, not a completed production session manager. They request a kernel-owned PID, exercise console output, report that filesystem/process/device/graphics services are unavailable, and exit with status 78. They do not print a readiness marker. Consequently, ELF structural checks may pass while runtime acceptance must still fail; do not publish an ISO until the actual target service flows and all six full-ISO cases pass.
