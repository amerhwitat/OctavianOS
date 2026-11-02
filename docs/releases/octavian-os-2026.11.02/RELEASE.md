# OctavianOS — live ISO 2026-11-02

Bootable amd64 live image built from this repository's `live-image/build.sh`.

| Field | Value |
| --- | --- |
| File | `octavian-os-live-amd64.iso` |
| Size | 488,302,592 bytes (466 MiB) |
| SHA-256 | `41bba4d3b3b4a6cb46e025792b36458ec82ea78936fb52157fcc32d3050785ea` |
| Volume label | `OCTAVIAN_OS` |
| Kernel | Debian `6.12.107+deb13-amd64` |
| Root filesystem | squashfs, xz + x86 BCJ, 1 MiB blocks, 423,084,032 bytes |
| Firmware | BIOS (El Torito) and UEFI (`efi.img`), GRUB 2.12 |
| Source commit | `5143470` |
| Built | 2026-11-02 UTC on 2 vCPU sandbox (Debian 13 trixie, 2 vCPU) |
| Packages | 484 |

## Download

- ISO — https://github.com/amerhwitat/OctavianOS/releases/download/octavian-os-2026.11.02/octavian-os-live-amd64.iso
- Release page (checksums + notes) — https://github.com/amerhwitat/OctavianOS/releases/tag/octavian-os-2026.11.02

## What boots

`live-boot` mounts the squashfs and hands off to systemd. tty1 auto-logs in as `live` and
starts X with the Aurora WebKit kiosk (`/usr/local/bin/aurora-session`), which renders this
project's own HTML desktop fullscreen. A second GRUB entry boots a plain openbox + xterm
session (`session=classic`); `nomodeset` and verbose entries cover difficult hardware.
Text console login `live` / `live` (root password `live`), passwordless sudo for `live`.

## Contents

- `/opt/aurora/desktop` — the project's HTML desktop, patched at build time with the shipped wallpaper set.
- `/opt/aurora/wallpapers` — 26 offline wallpapers (2560 px JPEG), mirrored to `/usr/share/backgrounds/`.
- `/opt/aurora/repo` — verbatim snapshot of this repository at the build commit.
- `/opt/aurora/PROJECT.md` — provenance record written by the build.

## What this image is not

The ISO boots the Debian Linux kernel, not the project's native Spit Fire/Koronos kernel.
It exercises the Aurora desktop, applications and userspace payload on real hardware; it is
**not** evidence that the native kernel reaches a verified userspace handoff. Those
acceptance gates remain tracked separately in `docs/`.

## Verification performed 2026-11-02

- squashfs superblock read back (xz, 1 MiB blocks, exportable) and payload spot-checked inside it.
- El Torito catalog lists both a BIOS `eltorito.img` and a UEFI `efi.img` entry.
- QEMU serial boot of the finished ISO reached the login prompt (see `BUILD.log` / `BOOT-QEMU.log`).
- The GitHub release asset reports the same SHA-256 as this file (server-computed digest).
