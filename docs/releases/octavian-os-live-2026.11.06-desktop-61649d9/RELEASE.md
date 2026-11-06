# OctavianOS live ISO 2026.11.06 (28-wallpaper desktop build)

- Release: [octavian-os-live-2026.11.06-desktop-61649d9](https://github.com/amerhwitat/OctavianOS/releases/tag/octavian-os-live-2026.11.06-desktop-61649d9)
- Source commit: `61649d9`
- Image: `octavian-os-live-amd64.iso`
- Size: 514,764,800 bytes (491 MiB)
- SHA-256: `eb8b201116763702ca58e203a3493f52a5e9e56ba9f7bb5f312db4d00e2b41f1`
- Boot targets: BIOS (El Torito) and UEFI (`/efi.img`), serial console on every entry
- GRUB: `set timeout=300` with `set timeout_style=menu` — Jasper, Gates, Aurora, Classic X,
  Safe graphics and Verbose entries wait for an explicit choice
- Wallpapers: 28 (wp01-wp28), including the two supplied desktop reference images
- Desktop: Aurora shell (Jasper/Windows 12, Gates/macOS, Aurora/Linux 7.x profiles) with
  VoiceConnect and the Network Applications panel

## Verification for this build

- `live-image/build.sh` completed the full pipeline (payload staging, SDK report, squashfs, ISO).
- `/boot/grub/grub.cfg` extracted from the image shows the 300 s menu and all profile entries.
- Release asset re-downloaded over HTTPS: HTTP 200, size matches the uploaded object.

Scope: the image boots a Debian Linux kernel with the project's own userland and desktop. It is
not a native Koronos release; the native ring-3 gate is tracked separately in
`docs/PRODUCTION_USERSPACE_HANDOFF.md`.
