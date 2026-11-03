#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
SOURCE="$ROOT/vendor/chimera-ii-os/source"
ASSET="$SOURCE/desktop/aurora/assets/Init.mp4"
LIBRARY_ASSET="$SOURCE/desktop/aurora/assets/library/Init.mp4"
BUILD="$ROOT/live-image/build.sh"
GRUB="$ROOT/boot/iso/grub.cfg"
SPLASH="$SOURCE/desktop/aurora/aurora-init-splash.sh"

test -s "$ASSET" || { echo "canonical Init.mp4 is missing" >&2; exit 1; }
test -s "$LIBRARY_ASSET" || { echo "library Init.mp4 copy is missing" >&2; exit 1; }
cmp -s "$ASSET" "$LIBRARY_ASSET" || { echo "Init.mp4 asset copies differ" >&2; exit 1; }
grep -Fq 'INIT_VIDEO_SOURCE="$NATIVE_SOURCE/desktop/aurora/assets/Init.mp4"' "$BUILD"
grep -Fq 'INIT_VIDEO_SOURCE="$NATIVE_SOURCE/desktop/aurora/assets/library/Init.mp4"' "$BUILD"
grep -Fq 'generated substitutes are disabled' "$BUILD"
! grep -Fq 'ffmpeg -hide_banner -loglevel error -y' "$BUILD"
grep -Fq 'install -m 0644 "$INIT_VIDEO_SOURCE" "$WORK/usr/share/chimera/aurora/assets/Init.mp4"' "$BUILD"
grep -Fq 'for boot_stage in visual spitfire jasper grub; do' "$BUILD"
grep -Fq 'install -D -m 0644 "$INIT_VIDEO" "$ISODIR/boot/$boot_stage/Init.mp4"' "$BUILD"
grep -Fq 'init-video-manifest.json' "$BUILD"
grep -Fq 'CHIMERA_INIT_VIDEO=/usr/share/chimera/aurora/assets/Init.mp4' "$BUILD"
grep -Fq 'CHIMERA_SPLASH_MAX_SECONDS=12' "$BUILD"
grep -Fq 'aurora-init-splash.sh' "$BUILD"
grep -Fq 'mpv --fs' "$SPLASH"
grep -Fq 'Boot intro media found (GRUB does not play MP4 itself)' "$GRUB"
grep -Fq 'openbox --sm-disable' "$BUILD"
grep -Fq 'Openbox window manager ready' "$BUILD"
grep -Fq 'exec /usr/local/bin/chimera-boot-mode' "$BUILD"
echo "Init.mp4 source identity, boot-stage staging, GRUB limitation and Aurora session playback contract: PASS"
