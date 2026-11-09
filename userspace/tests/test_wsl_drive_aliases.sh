#!/usr/bin/env bash
set -euo pipefail
ROOT="$(mktemp -d)"
trap 'rm -rf "$ROOT"' EXIT
mkdir -p "$ROOT/mnt/c/Users" "$ROOT/mnt/d/Projects"
CHM_WSL_FORCE=1 CHM_MNT_ROOT="$ROOT/mnt" CHM_DRIVE_ROOT="$ROOT/mnt/drive" \
  bash "$(dirname "$0")/../bin/octavian-map-windows-drives"
test -L "$ROOT/mnt/drive/C"
test "$(readlink "$ROOT/mnt/drive/C")" = "$ROOT/mnt/c"
test -L "$ROOT/mnt/drive/D"
test "$(readlink "$ROOT/mnt/drive/D")" = "$ROOT/mnt/d"
# Idempotence: a second pass preserves the original links.
CHM_WSL_FORCE=1 CHM_MNT_ROOT="$ROOT/mnt" CHM_DRIVE_ROOT="$ROOT/mnt/drive" \
  bash "$(dirname "$0")/../bin/octavian-map-windows-drives"
test "$(readlink "$ROOT/mnt/drive/C")" = "$ROOT/mnt/c"
# Never replace a pre-existing directory or file.
mkdir "$ROOT/mnt/drive/E"
mkdir "$ROOT/mnt/e"
if CHM_WSL_FORCE=1 CHM_MNT_ROOT="$ROOT/mnt" CHM_DRIVE_ROOT="$ROOT/mnt/drive" \
  bash "$(dirname "$0")/../bin/octavian-map-windows-drives"; then
  echo "expected conflict rejection" >&2
  exit 1
fi
test -d "$ROOT/mnt/drive/E"
echo "PASS: WSL drive aliases, idempotence, and conflict protection"
