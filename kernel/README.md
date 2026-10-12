# Kernel source and release gate

The full Koronos kernel source has not yet been imported into this destination tree. Do not publish a release ISO by substituting a documentation file, mock binary, or the host kernel.

## Required kernel deliverables

- `kernel/koronos/`: boot entry, architecture setup, exceptions/interrupts, scheduler and process runtime.
- `kernel/arch/x86_64/`: x86_64 boot handoff and hardware setup.
- `kernel/arch/aarch64/`: independent ARM64 boot handoff for mobile-capable builds.
- `kernel/microkernel/`: IPC, address-space/process isolation, capability policy and service supervision.
- `kernel/abi/`: versioned boot information, `chm.mode` / `chm.desktop` parsing, module handoff and userspace ELF admission.
- `kernel/tests/`: host tests plus QEMU serial/readiness acceptance tests.

The release workflow fails closed unless a real kernel ELF and required userspace payloads pass the ISO contract. A passing C unit test is not a boot test; a booted kernel is not a ready desktop.

## Migration source

Upstream: https://github.com/amerhwitat/ChimeraIIOS

Use the dedicated `OCTAVIANOS_IMPORT_TOKEN` Actions secret only for the history importer. Do not place credentials in source or logs. Port code with provenance and license metadata; do not flatten all source repositories into one tree.
