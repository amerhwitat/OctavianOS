# OctavianOS 2026.11.02 (fullscreen desktop fix) — live ISO octavian-os-live-2026.11.02-desktop-4f9f4c89a2cb

Rebuild of the 2026.11.02 live image on top of `4f9f4c89a2cb` with the desktop
fullscreen fix: the Aurora kiosk now fills the screen under Openbox at 1280x720 and
1920x1080 (verified), instead of rendering at its intrinsic size.

Source tree also carries the 26 attached wallpapers introduced in 5143470 and the offline application catalogs staged in 4f9f4c8.

| Field | Value |
| --- | --- |
| File | `octavian-os-live-amd64.iso` |
| Size | 485,312,512 bytes (463 MiB) |
| SHA-256 | `1904f9c055321122cabfad5e6d13a89a21243c0a56c7cf9bdfca8efb9dd90eed` |
| Volume label | `OCTAVIAN_OS` |
| Kernel | Debian `6.12.107+deb13-amd64` |
| Firmware | BIOS (El Torito) + UEFI (`efi.img`), GRUB 2.12 |
| Source commit | `4f9f4c89a2cb` |

## Download

- ISO — https://github.com/amerhwitat/OctavianOS/releases/download/octavian-os-live-2026.11.02-desktop-4f9f4c89a2cb/octavian-os-live-amd64.iso
- Release page — https://github.com/amerhwitat/OctavianOS/releases/tag/octavian-os-live-2026.11.02-desktop-4f9f4c89a2cb
- Download index (both editions, checksums, wallpapers) — https://amerhwitat.github.io/downloads/#live-isos
- Superseded build — https://github.com/amerhwitat/OctavianOS/releases/tag/octavian-os-2026.11.02

## Contents

- `/opt/aurora/desktop` — the project's HTML desktop, patched at build time, now launched fullscreen.
- `/opt/aurora/wallpapers` — 26 offline wallpapers (2560 px JPEG), mirrored to `/usr/share/backgrounds/`.
- `/opt/aurora/repo` — verbatim source snapshot at the build commit, including the offline app catalogs.
- `/opt/aurora/PROJECT.md` — provenance record written by the build.

## Boot

GRUB entries: "Live desktop" (Aurora kiosk), "Classic X session (openbox)", "Safe graphics (nomodeset)",
"Verbose boot". Live login `live` / `live`, root `live`, passwordless sudo. BIOS and UEFI both supported;
the attached `ISO-BOOT-REPORT.txt` is the El Torito/GPT/APM map read back from the published image.

## Scope

The image runs the Debian Linux kernel with this repository's Aurora desktop and userspace payload. It is
not a build of the native Spit Fire/Koronos kernel and does not discharge the native userspace-handoff
acceptance gates tracked in `docs/`. Third-party catalog entries are not installed or certified
applications unless stated.

## Verification (2026-11-03)

- Published `.sha256` asset matches the released file byte for byte (`1904f9c055321122…`), size 485,312,512 bytes.
- Both download URLs return the ISO directly (HTTP 302 → 200, correct `content-length`).
- Boot report confirms BIOS `eltorito.img` plus UEFI `efi.img` hybrid layout with GPT/APM entries.
