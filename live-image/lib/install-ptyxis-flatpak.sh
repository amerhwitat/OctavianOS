#!/usr/bin/env bash
set -Eeuo pipefail

ROOTFS="${1:?usage: install-ptyxis-flatpak.sh ROOTFS [WORK_DIR]}"
WORK="${2:-$ROOTFS/var/tmp/ptyxis-flatpak}"
FLATPAK_SYSTEM_DIR="$ROOTFS/var/lib/flatpak"

command -v flatpak >/dev/null 2>&1 || { echo "[PTYXIS] host flatpak CLI is required" >&2; exit 2; }
[[ -x "$ROOTFS/usr/bin/flatpak" ]] || { echo "[PTYXIS] target rootfs is missing /usr/bin/flatpak; add flatpak and its dependencies first" >&2; exit 2; }

mkdir -p "$FLATPAK_SYSTEM_DIR" "$ROOTFS/usr/local/bin" "$ROOTFS/usr/share/chimera/aurora" "$WORK"
export FLATPAK_SYSTEM_DIR

# Flathub's signed remote configuration supplies its GPG key. No --no-gpg-verify
# option is used; flatpak install must verify the signed app and runtime commits.
flatpak remote-add --system --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install --system --assumeyes --noninteractive flathub app.devsuite.Ptyxis

location="$(flatpak info --system --show-location app.devsuite.Ptyxis)"
commit="$(flatpak info --system --show-commit app.devsuite.Ptyxis)"
runtime="$(flatpak info --system --show-runtime app.devsuite.Ptyxis)"
ref="$(flatpak info --system --show-ref app.devsuite.Ptyxis)"
IFS=/ read -r ref_kind ref_app arch ref_branch <<< "$ref"
[[ "$ref_kind" == "app" && "$ref_app" == "app.devsuite.Ptyxis" && "$ref_branch" == "stable" && -n "$commit" && -n "$runtime" && -n "$arch" ]] || { echo "[PTYXIS] Flatpak metadata is incomplete" >&2; exit 2; }
case "$location" in
  "$FLATPAK_SYSTEM_DIR"/app/app.devsuite.Ptyxis/*) ;;
  *) echo "[PTYXIS] Flatpak app resolved outside target rootfs: $location" >&2; exit 2 ;;
esac
[[ -x "$location/files/bin/ptyxis" ]] || { echo "[PTYXIS] signed Flatpak commit has no ptyxis executable" >&2; exit 2; }

cat > "$ROOTFS/usr/local/bin/ptyxis" <<'EOF'
#!/bin/sh
exec /usr/bin/flatpak run --system --branch=stable app.devsuite.Ptyxis "$@"
EOF
chmod 0755 "$ROOTFS/usr/local/bin/ptyxis"

wrapper_sha="$(sha256sum "$ROOTFS/usr/local/bin/ptyxis" | awk '{print $1}')"
app_sha="$(sha256sum "$location/files/bin/ptyxis" | awk '{print $1}')"
python3 - "$ROOTFS/usr/share/chimera/aurora/ptyxis-flatpak-provider.json" "$commit" "$runtime" "$arch" "$location" "$wrapper_sha" "$app_sha" <<'PY'
import json, pathlib, sys
path, commit, runtime, arch, location, wrapper_sha, app_sha = sys.argv[1:]
report = {
    "schema": "chimera-flatpak-terminal-provider/v1",
    "provider": "ptyxis",
    "app_id": "app.devsuite.Ptyxis",
    "remote": "flathub",
    "branch": "stable",
    "commit": commit,
    "runtime": runtime,
    "architecture": arch,
    "signature_verified": True,
    "installation_location": location,
    "wrapper_path": "/usr/local/bin/ptyxis",
    "wrapper_sha256": wrapper_sha,
    "app_binary_path": location + "/files/bin/ptyxis",
    "app_binary_sha256": app_sha,
}
pathlib.Path(path).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
PY

echo "[PTYXIS] staged signed Flathub app.devsuite.Ptyxis commit=$commit runtime=$runtime arch=$arch"
