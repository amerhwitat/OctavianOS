# Boot target-to-userspace audit

The destination repository's current source-level routing trace is maintained in [BOOT_SEQUENCE_TRACE.md](BOOT_SEQUENCE_TRACE.md). This document records the current audit status and key limitations.

## Scope

The OctavianOS tree now has explicit GRUB/Jasper configfiles for Live Aurora, Live Marine, native Installer, Recovery, Diagnostics, Safe Graphics, Spit Fire routing, the optional Retro/Emulator Center, and the Installation menu alias. Every tracked `configfile /boot/...cfg` edge is checked by `tests/boot/test_boot_target_graph.py`. The CI workflow also runs `grub-script-check` over tracked GRUB configs and the existing installer payload-routing test.

## Current routing contracts

- **Live Aurora:** Koronos ELF + Live initramfs + Live manifest, with `chm.desktop=aurora` and the desktop selection manifest.
- **Live Marine:** same Live payload with `chm.desktop=marine`.
- **Installer:** top-level GRUB routes to `boot/jasper/install.cfg`; the native path requires the installation image, manifest, contract, phases and profiles and passes them to Koronos under legacy ABI module names.
- **Recovery / Diagnostics:** use the recovery initramfs and manifest, with explicit mode arguments.
- **Safe Graphics:** direct target requests `chm.mode=safe chm.graphics=basic`.
- **Spit Fire:** acts as a menu adapter into target-specific configs and Jasper.
- **Retro / Last Known Good / ARM64:** do not claim support if the optional payload, rollback snapshot, or architecture-specific kernel is missing.

## Important unresolved runtime handoffs

- The Live userspace must parse `chm.desktop=aurora|marine`, validate its session manifests, launch the chosen desktop and emit a real readiness marker. A GRUB menu entry or HTML prototype is not proof of native session launch.
- Koronos must classify all Multiboot2 module names and execute the selected userspace. The earlier source audit found process admission in **load-plan mode**; an admitted ELF record is not an executed process.
- The installer must display its UI, inventory storage, show a reviewed plan, require explicit confirmation, and invoke a safe platform backend. The config's module list is not proof that installation succeeds.
- Recovery and diagnostics need an observable shell/service startup even when graphics initialization fails.
- Runtime payload files referenced by GRUB are generated/imported ISO assets and are not all tracked in this destination tree. The ISO builder must stage them, verify hashes and architecture, and fail the build when a required target payload is missing.

## Verification status

- Configfile graph and target IDs: static test added; CI result pending until the workflow runs on this branch.
- GRUB parser check: added to the workflow; result pending.
- ISO asset existence and rebuilt ISO: not verified.
- QEMU/physical boot, actual Koronos userspace execution, Aurora/Marine session readiness, installer disk operations: not verified.
- ISA conformance: separate test track; cataloged instructions are not necessarily executable or conformant.

Never infer boot success from labels, progress messages, a passing source-level routing test, or a successful ISO build alone.

## Production userspace acceptance update (2026-10-19)

The latest inspected complete ISO workflow is [run 39185798999](https://github.com/amerhwitat/OctavianOS/actions/runs/39185798999). Its native Koronos build, Multiboot2/target-routing smoke tests, full ISO kernel-readiness smoke, and candidate artifact upload completed successfully. The separate **Verify real Live, Installer, and Recovery userspace** job failed for all three target traces with the same failure previously seen in [run 39183883211](https://github.com/amerhwitat/OctavianOS/actions/runs/39183883211):

`FAIL: missing user-originated init syscall acknowledgement (CPL 3), actual init PID readiness marker`

The prerelease publication job was skipped. Thus this run proves kernel readiness and target routing, but not actual production init execution. It does not establish separate BIOS and UEFI PASS/FAIL results for each target; those six cases remain NOT VERIFIED. Aurora after real Live init, installer completion/installed boot, and an actual Recovery action also remain NOT VERIFIED.

See [PRODUCTION_USERSPACE_HANDOFF.md](PRODUCTION_USERSPACE_HANDOFF.md) for the required payload extraction, target selection, page-table and TSS setup, ring-3/syscall path, PID/exit semantics, and acceptance sequence. Do not weaken `tests/migration/verify-userspace-handoff.py` or synthesize readiness markers to make the gate green.
