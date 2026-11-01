# QEMU acceptance marker contract

Each native target must emit a stable serial marker only after the named component has actually initialized:

- `OCTAVIANOS_KERNEL_READY`: kernel initialization, exception/interrupt setup and scheduler started.
- `OCTAVIANOS_USERSPACE_READY`: selected userspace ELF admitted and executing; desktop targets also require session manager and compositor readiness.
- `OCTAVIANOS_INSTALLER_READY`: installer UI and storage safety checks are active.
- `OCTAVIANOS_RECOVERY_READY`: recovery environment and diagnostic shell are active.
- `OCTAVIANOS_DIAGNOSTICS_READY`: diagnostics services are active.

The QEMU workflow deliberately fails when a real ISO or readiness marker is missing. A GRUB menu appearing is not a passing boot test. The current repository does not yet include the full native kernel/userspace payload required for this test.
