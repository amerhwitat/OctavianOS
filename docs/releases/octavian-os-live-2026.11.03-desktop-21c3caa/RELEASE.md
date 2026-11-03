# OctavianOS Live ISO 2026.11.03 (26-wallpaper build)

- Release: [octavian-os-live-2026.11.03-desktop-21c3caa](https://github.com/amerhwitat/OctavianOS/releases/tag/octavian-os-live-2026.11.03-desktop-21c3caa)
- Source commit: `21c3caaa3105eae0a0e211b843c1ef7412d7b8f5`
- Image: `octavian-os-live-amd64.iso`
- Size: 488,323,072 bytes (466 MiB)
- SHA-256: `bce639295832bbe84152b7c1b0a1ce667ba3607ef1f0fa77abea64a1ba823531`
- Boot targets: BIOS (El Torito, grub2-mbr) and UEFI (`/efi.img`)
- Wallpapers: 26 (wp01–wp26), default background plus picker
- Desktop: `desktop/aurora-wayland-glass/index.html` fullscreen in the Aurora kiosk under Openbox
- Boot entries: Live desktop, Classic X session, Safe graphics (`nomodeset`), Verbose, all with
  `console=tty0 console=ttyS0,115200n8`

Boot verification (this build): ISO structure and GRUB configuration verified from the image
(6 menu entries, serial console on every Linux entry); the identical builder's Chimera image
was booted to a userspace login prompt in QEMU for this release cycle.

Scope note: Debian Linux kernel plus the OctavianOS userland and desktop. Not a native Koronos
release; the native handoff gate in `docs/PRODUCTION_USERSPACE_HANDOFF.md` is unchanged.
