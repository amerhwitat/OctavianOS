# Desktop wallpaper and boot artwork

This catalog distinguishes original local artwork from optional remotely hosted Unsplash photos. Local source art can work offline in the desktop prototype; bootloader display requires a raster derivative packaged on the ISO.

## Aurora Wayland Glass Desktop

- **Octopus Aurora** — original local vector artwork at `desktop/aurora/assets/octavian-octopus-aurora.svg`.
- **Eventide Nebula** — original cinematic boot/loading backdrop at `desktop/aurora/assets/octavian-boot-nebula.svg`.
- **Deep Signal** — original low-contrast diagnostic/log backdrop at `desktop/aurora/assets/aurora-diagnostics-backdrop.svg`.

## Jasper / GRUB

- **The Seven Gates** — original boot-menu artwork at `desktop/aurora/assets/jasper-gates-boot.svg`, designed with dark negative space for legible menu text.

All four local SVG assets are original project artwork dedicated to OctavianOS under CC0-1.0. See `desktop/aurora/assets/octavian-artwork-manifest.json` and `boot/jasper/GRAPHICS_AND_ARTWORK.md`.

## Optional Unsplash prototype photos

- **Green aurora over a calm ocean** — Kristaps Ungurs. Source: https://unsplash.com/photos/aurora-borealis-over-calm-ocean-2xx7so0d3cY
- Direct image: https://images.unsplash.com/photo-1786335091902-eb0166246cbe?auto=format&fit=crop&w=2400&q=85
- **Sea turtle over coral reef** — Kristin Hoel. Source: https://unsplash.com/photos/a-sea-turtle-swimming-over-a-coral-reef-pyw39Zn6wWo
- Direct image: https://images.unsplash.com/photo-1717293520171-b1d8b5d5e3f2?auto=format&fit=crop&w=2400&q=85

Both source pages identify the photos as free to use under the [Unsplash License](https://unsplash.com/license). Official guidance: https://help.unsplash.com/en/articles/2612315-can-i-use-unsplash-images-for-personal-or-commercial-projects

## Offline packaging

Remote wallpapers require internet and may be unavailable or rate-limited. Prefer local assets for boot/live/installer/recovery media. Run `tools/artwork/prepare-boot-artwork.sh` in the ISO build environment to create PNG derivatives. The current source addition does not prove the production ISO build invokes that script or embeds the resulting files; wire it into the actual ISO builder and validate both BIOS and UEFI media before claiming boot-menu artwork is active. Do not reintroduce the obsolete aurora-background.jpg convention; keep its absence covered by the desktop artwork regression test.

For menu and log legibility, preserve a dark translucent overlay and do not bake essential status text into the image. Use a local fallback gradient when remote desktop images fail to load.
