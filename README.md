# OctavianOS

OctavianOS is the successor identity for the ChimeraIIOS operating-system research project. This repository is the destination for the source/history migration, build pipeline, boot/runtime work, ISA catalog, and Aurora desktop.

## Migration status

A GitHub Actions importer is being staged to preserve the source repository's branches and tags under `chimera-import/*` refs. This keeps the original project untouched and avoids overwriting the destination bootstrap branch. Imported source history is not the same as a completed rename; the OctavianOS working tree and builds must still be migrated and validated.

- Source repository: https://github.com/amerhwitat/ChimeraIIOS
- Required boot path: **Spit Fire → Jasper/GRUB → Koronos ELF → hardware/driver initialization → scheduler/runtime loop → live/recovery/installer userspace → Aurora**
- Build outputs must be rebuilt and tested; renaming an artifact is not validation.
- Installer and recovery acceptance requires observable userspace execution in QEMU, not just payload classification.
- ISA status must distinguish documented, cataloged, encoded/decoded, executed, and conformance-tested.

## Native N-bit architecture

The architectural target is an 8192-bit default *software-defined* native execution model, configurable to N bits. It requires explicit-width integer/register abstractions, architecture profiles, ABI and memory-layout rules, and checked adapters for physical ISA backends. An 8192-bit register model does not imply that x86-64, ARM64, or other physical CPUs directly execute 8192-bit instructions; physical backends must lower, emulate, or trap unsupported operations honestly.

The implementation is not complete until arithmetic/flags, decoding, memory addressing, exceptions/traps, privilege, context switching, and conformance tests pass for each declared profile.

## Engineering gates

Do not claim a target GUI or installer works until the boot menu target, staged payload, kernel handoff, userspace entry, and GUI process have been traced and exercised in automated boot tests. Do not mark an ISA as implemented based only on a catalog entry or metadata.


## Engineering notes

- [Migration runbook](docs/MIGRATION_RUNBOOK.md) — required GitHub token permissions and history-preserving import procedure.
- [Boot target audit](docs/BOOT_TARGET_AUDIT.md) — source-level target-to-payload trace and QEMU acceptance gates.
- [Native N-bit model](docs/architecture/NBIT_NATIVE_MODEL.md) — configurable register substrate, tests, and limitations.
