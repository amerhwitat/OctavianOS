# Jasper / GRUB graphics and artwork integration

**Status: source assets and configuration guidance added; ISO integration and runtime resolution remain unverified.**

## Display contract

Use the best graphics mode actually advertised by the firmware/GRUB video backend, then fall back through common SVGA modes. Never assume every display supports 1920×1080 or 32-bit color. The candidate mode order is:

`2560x1440x32,1920x1080x32,1600x900x32,1366x768x32,1280x1024x32,1024x768x32,800x600x32,640x480x32,auto`

The practical SVGA compatibility floor is 1024×768, with 640×480 as the final recovery mode. If the firmware/GRUB backend cannot establish a requested mode, GRUB must continue with a supported fallback rather than treating a mode request as proof that the kernel kept it.

## GRUB configuration guidance

The actual Jasper/GRUB configuration generator should set `gfxterm`, try the mode list above in `gfxmode`, and set `gfxpayload=keep` only where the selected boot protocol and Koronos framebuffer handoff preserve and validate the framebuffer. Include a text-console recovery entry. Do not hardcode an unsupported resolution and do not silently hide serial/debugcon output.

GRUB backgrounds must be a supported raster format (PNG, TGA, JPEG); SVG is source artwork only. Generate a PNG derivative during the ISO build, verify the file is readable by GRUB, and include it in both BIOS and UEFI media. A desktop/browser SVG loading successfully does not prove the bootloader can display it.

## Original artwork

- `desktop/aurora/assets/octavian-octopus-aurora.svg` — Aurora desktop wallpaper; existing original project art.
- `desktop/aurora/assets/octavian-boot-nebula.svg` — cinematic boot/loading backdrop with open negative space.
- `desktop/aurora/assets/jasper-gates-boot.svg` — Jasper boot/menu background, designed with a dark left column for menu readability.
- `desktop/aurora/assets/aurora-diagnostics-backdrop.svg` — low-contrast diagnostic/log background.

All new assets are original vector artwork dedicated to this project and may be used under CC0-1.0. Preserve contrast for menu text and logs; never burn essential status text into the artwork.

## Resolution must be proven end to end

A GRUB menu mode is only the first stage. Record the chosen mode and framebuffer dimensions in the Multiboot2/UEFI handoff, validate pitch/format/size in Koronos, and use a tested framebuffer console for progress bars and verbose logs during hardware initialization, scheduler startup, and userspace handoff. The kernel must fall back to a serial/debugcon or text console if framebuffer validation fails. The boot menu's selected resolution does not guarantee that the kernel or Aurora retains it.

## Acceptance checklist

- [ ] Build PNG derivatives and confirm GRUB can load them from the staged ISO.
- [ ] Confirm BIOS and UEFI GRUB both select the highest supported mode, then exercise 1024×768 and 640×480 fallback paths.
- [ ] Capture screenshots/logs at menu, Koronos init, runtime loop, and target userspace handoff.
- [ ] Verify progress/status updates continue throughout boot, not only in GRUB.
- [ ] Run unchanged Live/Installer/Recovery CPL 3 acceptance tests; graphics success must not substitute for userspace acceptance.
