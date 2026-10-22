# OctavianOS Mobile Edition

The mobile edition is a separate target, not a desktop menu alias. This folder defines the integration contract; an ARM64 kernel, drivers, and an emulator/device boot are required before calling it functional.

## Target layers

- ARM64 boot chain and device-tree/ACPI discovery as applicable.
- Microkernel services for IPC, process isolation, device management and power policy.
- Touch/display/input/audio/network/storage drivers.
- Mobile shell and application lifecycle service.
- Adaptive UI shared with the OctavianOS React Native companion.
- Package/signature verification, sandbox permissions, update/rollback and recovery.
- Desktop/mobile mode negotiation without loading x86_64 binaries on ARM64.

## Acceptance matrix

| Stage | Evidence required |
|---|---|
| Compile | ARM64 cross-build logs and warning-clean build |
| Emulate | QEMU virt/AArch64 or another documented target reaches kernel-ready marker |
| Userspace | Mobile shell and service readiness markers |
| Input/display | Touch or emulated input, display, rotation/resizing and focus tests |
| Recovery | Safe rollback and interrupted-update tests |
| Device | Hardware-specific test report, drivers and known limitations |

Do not report x86_64 ISO success as mobile support.


## Cross-edition synchronization and flash safety (2026-10-22)

OctavianOS Mobile follows the shared Chimera/Koronos release and artifact contract but remains an independently validated target. The Web/React Native companion is not the ARM64 kernel and cannot certify a device boot.

- Release records must bind repository/commit, architecture, device profile, boot mode, workflow run, SHA-256, and validation result. Never infer mobile support from x86_64 ISO or companion-app success.
- ARM64 remains in bring-up until a named device or documented QEMU AArch64 target proves kernel-ready, mobile-userspace-ready, display/input/audio/storage/network/power operation, verified-boot compatibility, update rollback and recovery. Other architectures remain unsupported until independently tested.
- Flash UI calls only the local native bridge; browser JavaScript cannot directly write block devices. Require a valid matching SHA-256, explicit target identity, typed destructive confirmation, native mounted-filesystem and system-disk refusal, and read-back verification.
- Generic phone ROM flashing stays disabled without an exact model-specific signed firmware profile. Never bypass bootloader locks, AVB, Apple secure boot or OEM signing. ADB/Fastboot checks remain read-only by default.
- Use PASS, FAIL, NOT RUN, or UNSUPPORTED rather than converting missing evidence into success. Release publication remains blocked by any required failed or missing production gate.
