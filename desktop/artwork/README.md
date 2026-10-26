# Desktop wallpaper artwork

The wallpaper catalog is offline-first. Aurora defaults to the tracked `desktop/aurora/assets/octavian-octopus-aurora.svg` artwork and Marine defaults to `desktop/marine/assets/marine-desktop.svg`. These local assets are packaged with the repository and do not require network access for desktop startup. Unsplash entries remain optional online enhancements only; the runtime must prefer each entry's `local_fallback` and never block boot waiting for a remote image.

## Aurora Wayland Glass Desktop

- **Green aurora over a calm ocean** — Kristaps Ungurs. Source: https://unsplash.com/photos/aurora-borealis-over-calm-ocean-2xx7so0d3cY
- Direct image used in prototype: https://images.unsplash.com/photo-1786335091902-eb0166246cbe?auto=format&fit=crop&w=2400&q=85

## Marine Desktop

- **Sea turtle over coral reef** — Kristin Hoel. Source: https://unsplash.com/photos/a-sea-turtle-swimming-over-a-coral-reef-pyw39Zn6wWo
- Direct image used in prototype: https://images.unsplash.com/photo-1717293520171-b1d8b5d5e3f2?auto=format&fit=crop&w=2400&q=85

Both source pages identify the photos as free to use under the [Unsplash License](https://unsplash.com/license). See the official license guidance: https://help.unsplash.com/en/articles/2612315-can-i-use-unsplash-images-for-personal-or-commercial-projects

## Production packaging

Prefer the checked-in local SVGs for offline desktop, installer and live-media startup. Keep remote URLs optional and use the catalog's `local_fallback` when unavailable; never require a network fetch to render a wallpaper. Do not reintroduce the obsolete `aurora-background.jpg` convention. ISO staging still needs explicit asset packaging and checksum validation for every shipped image.

Use responsive cover positioning and a dark translucent overlay so desktop icons remain legible. The catalog's local fallback paths are the source of truth for offline operation.

## Original OctavianOS artwork

The Aurora Wayland Glass Desktop prototype now uses the repository-local `../aurora/assets/octavian-octopus-aurora.svg` wallpaper instead of requiring a remote Unsplash image for its default background. The SVG is original project artwork; see `desktop/aurora/assets/octavian-artwork-manifest.json`. The Marine Desktop prototype's separate artwork remains unchanged.


## Bundled desktop artwork update

The Marine Desktop prototype now uses the original vector artwork at `desktop/marine/assets/marine-desktop.svg`; it does not fetch a remote Unsplash image at runtime. Aurora Wayland Glass continues to use `desktop/aurora/assets/octavian-octopus-aurora.svg`. Both prototypes offer a background picker that switches between these tracked assets and persists the choice in browser local storage. This improves offline design-preview reliability; ISO staging still needs explicit asset packaging and checksum validation.
