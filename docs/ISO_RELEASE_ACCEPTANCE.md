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


## Current fail-closed audit — 2026-11-05

**Production release: BLOCKED.** The checked-in diagnostic bundle
`docs/releases/octavian-native-2026.11.05/` must not be treated as proof of
production acceptance:

- The six trace files do not have a machine-generated provenance manifest
  binding every target/firmware trace to the same immutable ISO SHA-256.
- Live logs show a ring-3 text console probe, explicitly not a graphical
  desktop session; no Aurora or Marine readiness is demonstrated.
- Installer logs state that no block-device backend is present and that the
  run is a report-only dry-run; no installation, persistence, or reboot is
  demonstrated.
- Recovery logs state that the recovery initramfs is recognized but the
  native recovery init ELF/runtime handoff is withheld.
- The inspected logs report one logical CPU; no AP startup or overlapping
  execution is demonstrated.
- The native syscall trace does not establish the required VFS OPEN/READ/
  CLOSE and writable /tmp tests, process lifecycle, or signal delivery.

The readiness markers in those logs establish only that diagnostic probe
payloads ran. They do not clear the Live/Installer/Recovery production gates.
Do not publish this image as a production ISO. The legacy Linux-aligned
Octavian build is not a substitute for the native Koronos release path.

Next required work: implement and test the native VFS and block-device path,
QFS mount/write/recovery, real installer disk operations, recovery actions,
desktop sessions, AP/SMP, and process/syscall/signal lifecycle; then generate
six traces from one immutable ISO and have the unchanged fail-closed verifier
bind each trace to that ISO's SHA-256 before enabling release publication.


## Follow-up implementation/build audit — 2026-11-05

The x86-64 init payload now compiles with GNU assembler syntax and a per-build
musl sysroot. The static-PIE ELF contract test passed in run
[42083396378](https://github.com/amerhwitat/OctavianOS/actions/runs/42083396378).
That run then failed at `make install` because CMake used absolute
`/sbin` destinations and attempted to write into the CI host. The destinations
have been changed to relative `sbin`; rerun
[42083915601](https://github.com/amerhwitat/OctavianOS/actions/runs/42083915601)
is queued and has not yet validated the correction.

The current native userspace build matrix is deliberately x86-64 only.
ARM64 and RISC-V init entry sources and kernel user-entry contracts are absent;
the workflow must not package placeholder binaries as architecture support.

The Linux x86-64 syscall translation now maps the supported getpid/write/exit
calls into the stable Chimera syscall IDs. Fork, execve, wait4, mount, signal,
and other missing operations remain ENOSYS. The init no longer emits a generic
userspace-ready marker before mounts and service startup have succeeded. A
static-PIE build is not proof of a bootable or functional init process.

Filesystem capability claims are also fail-closed: the native installer profile
has an empty installable set until real native backends pass probe, format,
mount, read/write, sync, unmount, corruption and reboot tests. QFS still has
host-side formatter/inspection only; NTFS, XFS, FAT/exFAT, ext, Btrfs, ZFS and
other formats are not native Koronos drivers.

**Production remains BLOCKED.** The latest build, six same-ISO BIOS/UEFI target
traces, actual desktop sessions, installation/recovery postconditions, and
measured AP-backed SMP must all pass before any production release.
