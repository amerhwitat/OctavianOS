# Native OctavianOS release: porting and evidence checklist

This document is the execution checklist between the source snapshot and a release that can honestly be called bootable. A source import, container build, GRUB menu, or synthetic test is not proof of a native operating system.

## Required boot-to-desktop chain

Preserve the existing boot contract and artwork assets. The intended chain is:

**Spit Fire → Jasper/GRUB → Koronos ELF → hardware and driver initialization → scheduler/runtime loop → live/recovery/installer userspace → Aurora.**

Each transition must have a concrete artifact, a documented ABI/command-line contract, and a test that observes the next stage becoming ready. Do not substitute the hosted React desktop for native Aurora userspace.

## Phase 1 — import and inventory the upstream source

1. Run [Snapshot ChimeraIIOS source](https://github.com/amerhwitat/OctavianOS/actions/workflows/snapshot-chimera-source.yml) with `source_ref=main` and media inclusion set according to repository/storage policy.
2. Review the generated PR and `vendor/chimera-ii-os/SNAPSHOT-MANIFEST.json`. Confirm the recorded upstream commit and file count; inspect licenses and excluded generated/binary payloads.
3. Keep the imported tree isolated until components have explicit porting owners, dependencies, build instructions, and test evidence. The snapshot workflow deliberately does not preserve Git history or wire vendor files into active runtime paths.

## Phase 2 — port real executable payloads

The current release contract is defined in `boot/iso/target-payload-contract.json`. Build and stage real files; never create placeholders just to satisfy existence checks.

- [ ] Koronos kernel: `build/iso-root/boot/koronos/koronos.elf`; verify x86_64 ELF class/machine, entry point, and the GRUB/Multiboot2 contract.
- [ ] Live userspace: `build/iso-root/boot/live/chimera-live-initramfs.img`, `live-manifest.json`, and `desktop-sessions.json`.
- [ ] Installer: `build/iso-root/install/installer/installation.img`, manifest, installer contract, phases, and profiles.
- [ ] Recovery and diagnostics: `build/iso-root/boot/recovery/chimera-recovery-initramfs.img` and recovery manifest.
- [ ] Driver and device initialization: demonstrate enumerated devices and explicit failure handling when a required device/driver is unavailable.
- [ ] Scheduler/runtime: demonstrate task admission, context switch, timer interrupt handling, and a userspace handoff; do not equate a sequential simulation with SMP.
- [ ] Aurora native session: start from the live initramfs, report a readiness marker only after the compositor/session and input path are usable, and preserve the shared artwork contract.

For every payload, record source revision, reproducible build command, target architecture, SHA-256, dependencies, license, and test result. Update the manifest from build outputs, not by hand-asserting success.

## Phase 3 — validate each boot target independently

Run `python3 tools/boot/validate_iso_payloads.py --root build/iso-root` and `python3 tools/release/validate_release_inputs.py --root build/iso-root`. Both must pass against the actual staged root.

- [ ] Boot the built ISO in QEMU for Live Aurora.
- [ ] Boot Live Marine independently.
- [ ] Enter the installer and demonstrate a safe, explicit target-disk selection before any destructive operation.
- [ ] Enter recovery and diagnostics independently.
- [ ] Verify safe mode with basic graphics.
- [ ] Capture serial logs, QEMU command line, image hash, exit status, and target-specific readiness marker for each run.
- [ ] Test at least one documented UEFI path; test physical hardware separately before claiming hardware support.

QEMU acceptance must run against the actual release ISO and its target-specific readiness markers. A GRUB menu appearing is not a successful boot test. If the required payloads are absent, mark the target **blocked**, not passed.

## Phase 4 — release artifacts

The `release-artifacts.yml` workflow builds and smoke-tests the web desktop preview container, packages a Docker image tarball with SHA-256, and separately gates ISO creation/publication on the real native payloads.

- [ ] Run the workflow with a version such as `v0.1.0-preview.1` and `publish=true` only after all native payload gates pass.
- [ ] Confirm both the ISO and Docker tarball, plus their SHA-256 files, are attached to the GitHub Release.
- [ ] Download each asset and verify its checksum independently.
- [ ] Keep release notes precise: the Docker image is a hosted web desktop preview, not a kernel or mobile OS image.
- [ ] Do not create a release tag or claim a native release while the ISO job fails.

## Current status and evidence rules

The source snapshot is a reviewable import, not a port. The React/Vite web companion and Expo React Native source are separate hosted/mobile application deliverables. Neither implements the native kernel, native installer, native recovery, or a bootable mobile runtime.

A capability may be labeled **documented**, **cataloged**, **compiled**, **booted**, **userspace-ready**, **conformance-tested**, or **SMP-verified** only when the corresponding evidence exists. Missing evidence must remain explicitly marked as blocked or unverified.
