# Octavian retro emulator runtime

This directory adds a local-only launcher for Amiga and Commodore machines.

## Amiga A500 / A2000

Build the open-source PUAE libretro core:

```sh
./tools/retro/build-amiga-core.sh
```

Install RetroArch, then run `python3 tools/retro/bridge.py`. The bridge listens on
127.0.0.1:8766. Supply your own legally obtained Kickstart firmware and disk image.
The bridge accepts ADF/ADZ/DMS/FDI/IPF/HDF/HDZ/LHA/ZIP/M3U and supported CD formats.

## Commodore systems

Install the VICE emulator package for the host distribution. The bridge detects
`x64sc`, `x128`, `xvic`, `xplus4`, and `xpet`, and launches the selected
machine with `-autostart` using an argument vector (never a shell command string).
Supported disk/program extensions are validated per machine.

## Security and packaging

- The service binds only to loopback; it does not expose an emulator remotely.
- No copyrighted ROMs, Kickstart images, or commercial disk contents are bundled.
- Emulator binaries, firmware and user-owned disks remain local and are not deployed
  to GitHub Pages.
- A successful bridge health check only proves local provider discovery; launch and
  emulation still require runtime testing on the host.
