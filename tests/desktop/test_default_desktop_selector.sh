#!/usr/bin/env bash
set -Eeuo pipefail
root="$(mktemp -d)"
trap 'rm -rf "$root"' EXIT
export HOME="$root/home"
unset XDG_CONFIG_HOME
mkdir -p "$HOME"
bash vendor/chimera-ii-os/source/tools/desktop/set-default-desktop.sh freewin11
grep -qx 'default_desktop=freewin11' "$HOME/.config/chimera/desktop.conf"
bash vendor/chimera-ii-os/source/tools/desktop/set-default-desktop.sh freexp
grep -qx 'default_desktop=freexp' "$HOME/.config/chimera/desktop.conf"
if bash vendor/chimera-ii-os/source/tools/desktop/set-default-desktop.sh invalid; then exit 1; fi
echo "OctavianOS default desktop selector tests passed"
