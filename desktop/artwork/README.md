# Desktop wallpaper artwork

This catalog uses remotely hosted Unsplash photos as optional prototype wallpapers. Each entry links to the photographer's source page and the Unsplash License. The images remain hosted by Unsplash; this change does not claim that image binaries have been vendored into the repository or the ISO.

## Aurora Wayland Glass Desktop

- **Green aurora over a calm ocean** — Kristaps Ungurs. Source: https://unsplash.com/photos/aurora-borealis-over-calm-ocean-2xx7so0d3cY
- Direct image used in prototype: https://images.unsplash.com/photo-1786335091902-eb0166246cbe?auto=format&fit=crop&w=2400&q=85

## Marine Desktop

- **Sea turtle over coral reef** — Kristin Hoel. Source: https://unsplash.com/photos/a-sea-turtle-swimming-over-a-coral-reef-pyw39Zn6wWo
- Direct image used in prototype: https://images.unsplash.com/photo-1717293520171-b1d8b5d5e3f2?auto=format&fit=crop&w=2400&q=85

Both source pages identify the photos as free to use under the [Unsplash License](https://unsplash.com/license). See the official license guidance: https://help.unsplash.com/en/articles/2612315-can-i-use-unsplash-images-for-personal-or-commercial-projects

## Production packaging

Remote wallpapers require an internet connection and may be unavailable, changed, or rate-limited. For offline installer/live media, fetch the original image from its source page during a controlled asset-import step, verify the file and license, record its SHA-256 and attribution, and store it under the existing artwork contract. Do not reintroduce the obsolete aurora-background.jpg convention. The current change leaves the kernel/bootloader artwork pipeline untouched.

Use responsive cover positioning and a dark translucent overlay so desktop icons remain legible. Provide a local fallback gradient when remote loading fails.

## Original OctavianOS artwork

The Aurora Wayland Glass Desktop prototype now uses the repository-local `../aurora/assets/octavian-octopus-aurora.svg` wallpaper instead of requiring a remote Unsplash image for its default background. The SVG is original project artwork; see `desktop/aurora/assets/octavian-artwork-manifest.json`. The Marine Desktop prototype's separate artwork remains unchanged.


## Bundled desktop artwork update

The Marine Desktop prototype now uses the original vector artwork at `desktop/marine/assets/marine-desktop.svg`; it does not fetch a remote Unsplash image at runtime. Aurora Wayland Glass continues to use `desktop/aurora/assets/octavian-octopus-aurora.svg`. Both prototypes offer a background picker that switches between these tracked assets and persists the choice in browser local storage. This improves offline design-preview reliability; ISO staging still needs explicit asset packaging and checksum validation.
