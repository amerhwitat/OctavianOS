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
