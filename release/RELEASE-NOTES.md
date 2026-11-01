# OctavianOS / Chimera II OS — 1.0.0 (complete live app-runtime release)

**Artifact:** `OctavianOS-ChimeraII-1.0.0-amd64.iso`
**Size:** 900,200,448 bytes (858.5 MiB)
**SHA-256:** `65be61d3aeddcae155b2b1463de1291ab38901269618ae14fd9f86a1b253d523`
**Format:** Hybrid ISO 9660 — BIOS El Torito + UEFI El Torito + GPT/APM system area
**Kernel (Linux runtime):** Debian 6.1.0-50-amd64, live-boot SquashFS
**Kernel (native):** Koronos, freestanding x86-64 ELF64, Multiboot2
**Build system:** canonical `vendor/chimera-ii-os/source/build-chimera-iso.sh` in
`--host-rootfs` (Docker-free) mode

## What this release is

This is the first OctavianOS release that boots a **complete graphical userspace**
from the ISO and runs the repository's desktop environments and applications
offline. It carries two boot families on one hybrid image:

1. **Linux app-runtime targets** — a Debian `live-boot` SquashFS root with
   systemd, Xorg, Openbox and Chromium in kiosk mode. It serves the repository's
   desktops and applications from a local HTTP server at `127.0.0.1:8080` and
   renders them full-screen.
2. **Koronos native targets** — the original freestanding microkernel entries
   (`aurora-live`, `normal`, `install`, `recovery`, `diagnostics`, `safe-mode`,
   `last-known-good`, `retro`, `spitfire`, `jasper`) with the verified ring-3
   handoff probe.

## Verified in QEMU (BIOS, `-vga std`, TCG)

| Check | Result |
|---|---|
| Canonical `build-chimera-iso.sh --host-rootfs` end-to-end | **EXIT=0** |
| Hybrid El Torito (BIOS + UEFI) | PASS — `eltorito.img` + `efi.img` |
| `/live/vmlinuz`, `/live/initrd.img`, `/live/filesystem.squashfs` present | PASS |
| `live-boot` mounts the medium and assembles the overlay root | PASS |
| systemd reaches `graphical.target` | PASS |
| Aurora Wayland Glass desktop renders (welcome, menu bar, sidebar, dock) | PASS |
| Marine desktop renders (taskbar, Start launcher, ocean widgets) | PASS |
| Application Center renders (48 catalog entries) | PASS |
| Paint Studio launches (toolbar + drawing canvas) | PASS |
| All 5 app HTML surfaces + 2 desktops + web surface staged in SquashFS | PASS |

Screenshots captured from the running ISO are in `screenshots/` in the build
workspace: `boot-120s.png`, `after-enter.png` (Application Center),
`app-paint.png` (Paint Studio), `marine-desktop.png`.

## What was fixed to make this release

1. **Docker-free rootfs path.** `build-chimera-iso.sh` gained `--host-rootfs` /
   `CHIMERA_ROOTFS_MODE=host`, so the canonical 17-stage pipeline runs without
   Docker against a pre-populated rootfs.
2. **Missing init.** The Debian rootfs had no `/sbin/init`. The rootfs builder
   now installs `systemd systemd-sysv udev dbus` and guarantees
   `/sbin/init → /lib/systemd/systemd`.
3. **Clobbered coreutils.** The Chimera command-compatibility stage replaced
   `ls/cp/mv/rm/cat` in `/usr/bin` with `chimera-cmd` shims, breaking the distro.
   Host mode now sets `CHIMERA_COMMAND_NOCLOBBER=1`; real Debian binaries are
   preserved and `chimera-cmd` remains available under its own name.
4. **`findiso=` broke live-boot.** GRUB entries now use
   `boot=live live-media-path=/live`, which mounts the CD/USB medium directly.
5. **Kernel not staged on the ISO.** `build_squashfs()` now copies
   `/boot/vmlinuz-*` and `/boot/initrd.img-*` to `/live/vmlinuz` and
   `/live/initrd.img` before the rootfs is dropped.
6. **Repo build bugs.** Fixed the undefined `merge_commands()` call, the native
   multicall count (15, not 20), two `set -e`/`while read -d ''` loops, and the
   missing `.note.GNU-stack` section.

## Boot instructions

Write the ISO to a USB stick or attach it as a CD/DVD:

```sh
sudo dd if=OctavianOS-ChimeraII-1.0.0-amd64.iso of=/dev/sdX bs=4M status=progress oflag=sync
```

At the GRUB menu:

- **OctavianOS — Aurora Desktop (Linux app runtime: all apps)** — default
- **OctavianOS — Marine Desktop (Linux app runtime: all apps)**
- Chimera II OS native Koronos entries follow below.

The Linux runtime accepts `chm.desktop=aurora|marine` on the kernel command line.
The kiosk can be probed from a root shell with
`/opt/octavianos/probe-desktop.sh aurora`.

## What this release does NOT claim

- The Koronos native entries still launch the ring-3 validation probe, not the
  Aurora compositor natively. The graphical desktops run on the Linux runtime.
- Installer completion → reboot → installed-system boot is not yet automated.
- A real Recovery repair action and AP-backed SMP remain open.
- Full 8192-bit software ISA conformance remains open.

## Reproducing

```sh
cd vendor/chimera-ii-os/source
sudo bash tools/octavian-build-live-rootfs.sh          # debootstrap + runtime + staging
sudo env CHIMERA_ROOTFS_MODE=host CHIMERA_DROP_ROOTFS=1 \
  bash build-chimera-iso.sh --host-rootfs --clean-state
```

The resulting ISO is written to the source directory and copied to
`release/OctavianOS-ChimeraII-1.0.0-amd64.iso`.
