#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${OCTAVIAN_RETRO_BUILD_DIR:-$ROOT/.local/retro}"
SRC="$OUT/libretro-uae"
mkdir -p "$OUT/cores"
if [[ ! -d "$SRC/.git" ]]; then
  git clone --depth 1 https://github.com/libretro/libretro-uae.git "$SRC"
else
  git -C "$SRC" pull --ff-only
fi
make -C "$SRC" -j"$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 2)"
CORE="$(find "$SRC" -maxdepth 4 -type f -name '*_libretro.so' -print -quit)"
[[ -n "$CORE" && -s "$CORE" ]] || { echo "PUAE core output not found" >&2; exit 1; }
install -m 0755 "$CORE" "$OUT/cores/puae_libretro.so"
file "$OUT/cores/puae_libretro.so"
printf 'PUAE core ready: %s\n' "$OUT/cores/puae_libretro.so"
