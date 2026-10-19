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
