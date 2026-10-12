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
