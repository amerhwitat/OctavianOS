#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${1:-$ROOT/boot/jasper/artwork}"
mkdir -p "$OUT"
sources=(
  "$ROOT/desktop/aurora/assets/octavian-boot-nebula.svg"
  "$ROOT/desktop/aurora/assets/jasper-gates-boot.svg"
  "$ROOT/desktop/aurora/assets/aurora-diagnostics-backdrop.svg"
)
names=(octavian-boot-nebula jasper-gates-boot aurora-diagnostics-backdrop)
if command -v rsvg-convert >/dev/null 2>&1; then
  for i in "${!sources[@]}"; do
    rsvg-convert --format=png --width=1920 --height=1080 "${sources[$i]}" > "$OUT/${names[$i]}.png"
  done
elif command -v magick >/dev/null 2>&1; then
  for i in "${!sources[@]}"; do
    magick -background '#050b18' "${sources[$i]}" -resize '1920x1080!' "$OUT/${names[$i]}.png"
  done
elif command -v convert >/dev/null 2>&1; then
  for i in "${!sources[@]}"; do
    convert -background '#050b18' "${sources[$i]}" -resize '1920x1080!' "$OUT/${names[$i]}.png"
  done
else
  echo "ERROR: install rsvg-convert or ImageMagick (magick/convert) to rasterize GRUB artwork" >&2
  exit 2
fi
for f in "$OUT"/*.png; do
  test -s "$f" || { echo "ERROR: empty raster artwork: $f" >&2; exit 3; }
  file "$f"
done
echo "Artwork rasterized. ISO integration and BIOS/UEFI display still require separate validation."
