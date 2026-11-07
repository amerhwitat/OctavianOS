#!/bin/bash
# Reproducible live-image builder for the Aurora/Octavian desktop stack.
#
#   ./build.sh chimera      # Chimera II OS live ISO
#   ./build.sh octavian     # OctavianOS live ISO
#
# Optional environment:
#   BUILD_ROOT=/path   where the rootfs/work/ISO output lives (default: live-image/.build)
#   JOBS=n             squashfs/xz CPU count (default: nproc)
#   SKIP_DEBOOTSTRAP=1 reuse an existing base rootfs
#
# Requires (Debian/Ubuntu host): debootstrap xorriso squashfs-tools grub-pc-bin
# grub-efi-amd64-bin mtools dosfstools imagemagick python3 nasm gcc g++ make
# binutils file busybox-static cpio gzip.
set -euo pipefail

ED="${1:-}"
case "$ED" in
  chimera|octavian) ;;
  *) echo "usage: $0 <chimera|octavian>"; exit 2 ;;
esac

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMMAND_SOURCE="$REPO_DIR"
if [[ -f "$REPO_DIR/vendor/chimera-ii-os/source/tools/commands/generate_runtime_manifest.py" ]]; then
  COMMAND_SOURCE="$REPO_DIR/vendor/chimera-ii-os/source"
fi
python3 "$COMMAND_SOURCE/tools/commands/generate_runtime_manifest.py"
python3 -m json.tool "$COMMAND_SOURCE/system/commands/command-runtime-capabilities.json" >/dev/null

HERE="$REPO_DIR/live-image"
BUILD="${BUILD_ROOT:-$HERE/.build}"
BASE="$BUILD/rootfs-base"
WORK="${WORK_DIR:-$BUILD/rootfs-$ED}"
ISODIR="$BUILD/iso-$ED"
OUT="${OUT_DIR:-$BUILD/out}"
ART="$HERE/artwork"
JOBS="${JOBS:-$(nproc)}"

if [ "$(id -u)" -ne 0 ]; then
  exec sudo -E bash "${BASH_SOURCE[0]}" "$@"
fi

case "$ED" in
  chimera)
    TITLE="Chimera II OS"
    SHORT="chimera-ii"
    VOLID="CHIMERA_II_OS"
    ENTRY="desktop/index.html"
    DESKTOP_COPY="web"
    ISO_NAME="chimera-ii-os-live-amd64.iso"
    ;;
  octavian)
    TITLE="OctavianOS"
    SHORT="octavian"
    VOLID="OCTAVIAN_OS"
    ENTRY="desktop/aurora-shell/index.html"
    DESKTOP_COPY="desktop"
    ISO_NAME="octavian-os-live-amd64.iso"
    ;;
esac
VERSION="$(date -u +%Y.%m.%d)"
COMMIT="$(git -C "$REPO_DIR" rev-parse --short HEAD 2>/dev/null || echo snapshot)"
BRANCH="$(git -C "$REPO_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo main)"
REPO_URL="$(git -C "$REPO_DIR" config --get remote.origin.url 2>/dev/null | sed 's/\.git$//' || true)"
[ -n "$REPO_URL" ] || REPO_URL="https://github.com/amerhwitat/$(basename "$REPO_DIR")"

log() { printf '\n== [%s] %s\n' "$ED" "$*"; }

# ---------------------------------------------------------------- base rootfs
if [ ! -x "$BASE/bin/bash" ] || [ "${REBUILD_BASE:-0}" = "1" ]; then
  log "debootstrap trixie -> $BASE"
  rm -rf "$BASE"; mkdir -p "$BASE"
  debootstrap --arch=amd64 --variant=minbase \
    --include=apt-transport-https,ca-certificates,locales \
    trixie "$BASE" http://deb.debian.org/debian
fi

mount_chroot() {
  local T="${1:-$WORK}"
  mkdir -p "$T/proc" "$T/sys" "$T/dev/pts"
  mountpoint -q "$T/proc"    || mount -t proc proc "$T/proc"
  mountpoint -q "$T/sys"     || mount -t sysfs sys "$T/sys"
  mountpoint -q "$T/dev"     || mount --bind /dev "$T/dev"
  mountpoint -q "$T/dev/pts" || mount --bind /dev/pts "$T/dev/pts"
  cp -f /etc/resolv.conf "$T/etc/resolv.conf"
}
umount_chroot() {
  local T="${1:-$WORK}"
  for d in dev/pts dev sys proc; do
    mountpoint -q "$T/$d" && umount -l "$T/$d" || true
  done
}
trap 'umount_chroot "$WORK"; umount_chroot "$BASE"' EXIT

# ------------------------------------------------------------- package set
if [ ! -f "$BASE/.packages-installed-v4" ]; then
  log "installing shared package set (one-off)"
  mount_chroot "$BASE"
  cp "$COMMAND_SOURCE/tools/commands/install-command-providers.sh" "$BASE/tmp/chimera-install-command-providers.sh"
  DEBIAN_FRONTEND=noninteractive chroot "$BASE" /bin/bash -c '
    set -e
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq --no-install-recommends \
      linux-image-amd64 initramfs-tools live-boot live-boot-initramfs-tools \
      systemd systemd-sysv dbus dbus-x11 udev kbd console-setup \
      xserver-xorg-core xserver-xorg-legacy xserver-xorg-input-libinput \
      xserver-xorg-video-vesa xserver-xorg-video-fbdev xserver-xorg-video-cirrus \
      xinit xauth x11-xserver-utils x11-utils xfonts-base \
      python3 python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1 \
      libgl1 libglx-mesa0 libegl1 libgles2 \
      openbox xterm feh \
      fonts-dejavu-core fonts-liberation2 fonts-noto-core \
      sudo ca-certificates curl wget less nano htop pciutils usbutils file unzip xz-utils \
      iproute2 iputils-ping netbase procps psmisc rsync \
      e2fsprogs dosfstools parted gdisk alsa-utils kmod
      # Optional open-source shells and terminal emulators from signed Debian repositories.
      # Missing providers remain explicit in the generated manifest; no fake launchers.
      for item in \
        "xterm:xterm" "gnome-console:kgx" "gnome-terminal:gnome-terminal" \
        "blackbox-terminal:blackbox" "konsole:konsole" "ptyxis:ptyxis" \
        "xfce4-terminal:xfce4-terminal" "foot:foot" "kitty:kitty" \
        "alacritty:alacritty" "wezterm:wezterm" "ghostty:ghostty" "contour:contour" \
        "terminator:terminator" "tilix:tilix" "mate-terminal:mate-terminal" \
        "qterminal:qterminal" "sakura:sakura" "terminology:terminology" "lxterminal:lxterminal" \
        "bash:bash" "zsh:zsh" "fish:fish" "dash:dash" "mksh:mksh" \
        "yash:yash" "elvish:elvish" "nushell:nu"; do
        pkg="${item%%:*}"
        if apt-cache show "$pkg" >/dev/null 2>&1; then
          apt-get install -y -qq --no-install-recommends "$pkg" || echo "[AURORA-TERMINALS] package install failed: $pkg"
        else
          echo "[AURORA-TERMINALS] no Debian package candidate: $pkg"
        fi
      done
      # Runtime libraries for source-built GTK4/Wayland/Qt6 terminal providers.
      for pkg in \
        libgtk-4-1 libadwaita-1-0 libvte-2.91-0 libvte-2.91-gtk4-0 \
        libfcft4 libpixman-1-0 libutf8proc2 libjson-glib-1.0-0 libgee-0.8-2 \
        libxml2 librsvg2-2 libgraphene-1.0-0 libwayland-client0 libwayland-cursor0 \
        libxkbcommon0 libxkbcommon-x11-0 libx11-6 libx11-xcb1 libxcb1 \
        libxcb-render0 libxcb-shape0 libxcb-xfixes0 libxcb-cursor0 \
        libfontconfig1 libfreetype6 libharfbuzz0b libvulkan1 \
        libqt6core6t64 libqt6gui6t64 libqt6widgets6t64 libqt6qml6t64 libqt6quick6t64 \
        libdbus-1-3 libssl3 libasound2t64 libpulse0 libxrandr2 libxi6 \
        libxinerama1 libxcursor1 libxext6 libxrender1 libxfixes3 libxdamage1 libxcomposite1; do
        if apt-cache show "$pkg" >/dev/null 2>&1; then
          apt-get install -y -qq --no-install-recommends "$pkg" || echo "[AURORA-TERMINALS] runtime library install failed: $pkg"
        else
          echo "[AURORA-TERMINALS] no runtime library package candidate: $pkg"
        fi
      done
    bash /tmp/chimera-install-command-providers.sh
    rm -f /tmp/chimera-install-command-providers.sh
    apt-get clean
    rm -rf /var/lib/apt/lists/*
  '
  umount_chroot "$BASE"
  install -D -m 0644 "$COMMAND_SOURCE/system/commands/command-runtime-capabilities.json" "$BASE/usr/share/chimera/commands/command-runtime-capabilities.json"
  install -D -m 0644 "$COMMAND_SOURCE/tools/commands/os-command-runtime.json" "$BASE/usr/share/chimera/commands/os-command-runtime.json"
  # Build the actual C multicall ELF for this amd64 rootfs. The /usr/bin
  # chimera-cmd script is only an alias dispatcher and is never counted as
  # native implementation evidence.
  native_cmd="$BASE/usr/lib/chimera/chimera-cmd.native"
  native_bin_dir="$BASE/usr/lib/chimera/native-bin"
  mkdir -p "$(dirname "$native_cmd")" "$native_bin_dir" "$BASE/etc/profile.d"
  native_cc="${CHIMERA_NATIVE_CC:-${CC:-cc}}"
  command -v "$native_cc" >/dev/null 2>&1 || { echo "missing native command compiler: $native_cc" >&2; exit 2; }
  "$native_cc" -std=c11 -O2 -Wall -Wextra -Werror \
    "$COMMAND_SOURCE/src/chimera-command-compat/chimera-cmd.c" -o "$native_cmd"
  chmod 0755 "$native_cmd"
  for name in pwd echo ls cp mv touch mkdir rm cat clear whoami hostname date true false rmdir ln readlink basename dirname uname wc head tail sleep env printenv which seq yes tty id fold nl tr tee cmp; do
    ln -sfn ../chimera-cmd.native "$native_bin_dir/$name"
  done
  cat > "$BASE/etc/profile.d/chimera-native-commands.sh" <<'EOF_NATIVE_PATH'
# Prefer the explicitly tested Chimera C multicall entrypoints in user shells.
export PATH="/usr/lib/chimera/native-bin:$PATH"
EOF_NATIVE_PATH
  python3 "$COMMAND_SOURCE/tools/commands/verify-command-provider-coverage.py" "$BASE" "$COMMAND_SOURCE/system/commands/command-runtime-capabilities.json" x86_64
  python3 - "$BASE/usr/share/chimera/commands/command-provider-coverage.json" <<'PY_NATIVE_GATE'
import json, pathlib, sys
report=json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
native=[row for row in report["commands"] if row.get("mode")=="native"]
bad=[row["name"] for row in native if row.get("status")!="native-multicall-elf-and-entrypoint-present"]
if len(native)!=37 or bad:
    raise SystemExit(f"native command implementation gate failed: expected 37, found {len(native)}, missing={bad}")
print(f"Verified {len(native)} compiled native command entrypoints; external providers remain separately classified.")
PY_NATIVE_GATE
  touch "$BASE/.packages-installed-v4"
fi

# --------------------------------------------------------- command + ISA catalogues
# The vendor snapshot is the canonical source when present. Stage the actual
# source catalogues into the guest image (not just the generated capability
# summary) so both OS editions ship the same auditable command/ISA references.
CATALOG_DEST="$BASE/usr/share/chimera/catalogs"
catalog_files=(
  system/commands/chimera-command-list.json
  system/commands/ss64-command-catalog.json
  system/commands/compatibility-binary-policy.json
  system/commands/command-isa-coverage.json
  system/commands/command-runtime-capabilities.json
  tools/commands/os-command-runtime.json
  isa/catalog.json
  isa/generated/isa-encoding-registry.json
  ISA.csv
)
staged_catalogs=()
for rel in "${catalog_files[@]}"; do
  if [[ -s "$COMMAND_SOURCE/$rel" ]]; then
    install -D -m 0644 "$COMMAND_SOURCE/$rel" "$CATALOG_DEST/$(basename "$rel")"
    staged_catalogs+=("$rel")
  else
    echo "[CATALOG] unavailable source file (not fabricated): $rel"
  fi
done
if [[ -s "$REPO_DIR/system/commands/octavian-command-list.json" ]]; then
  install -D -m 0644 "$REPO_DIR/system/commands/octavian-command-list.json" "$CATALOG_DEST/octavian-command-list.json"
fi
if [[ -s "$REPO_DIR/catalogues/runtime-command-isa-contract.json" ]]; then
  install -D -m 0644 "$REPO_DIR/catalogues/runtime-command-isa-contract.json" "$CATALOG_DEST/runtime-command-isa-contract.json"
fi
for pair in \
  "runtime/commands/native-command-candidates.json:native-command-candidates.json" \
  "runtime/isa/universal-instruction-catalog.json:universal-instruction-catalog.json" \
  "runtime/isa/riscv-opcodes.json:riscv-opcodes.json"; do
  src="${pair%%:*}"
  dst="${pair#*:}"
  if [[ -s "$REPO_DIR/$src" ]]; then
    install -D -m 0644 "$REPO_DIR/$src" "$CATALOG_DEST/$dst"
  else
    echo "ERROR: generated command/ISA catalogue is missing: $REPO_DIR/$src" >&2
    exit 2
  fi
done
python3 - "$CATALOG_DEST" <<'PY_CATALOG_GATE'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
required = ("octavian-command-list.json", "catalog.json", "isa-encoding-registry.json", "native-command-candidates.json", "universal-instruction-catalog.json", "riscv-opcodes.json", "runtime-command-isa-contract.json", "command-isa-coverage.json")
missing = [name for name in required if not (root / name).is_file() or (root / name).stat().st_size == 0]
if missing:
    raise SystemExit("required command/ISA catalogue files missing: " + ", ".join(missing))
for path in root.glob("*.json"):
    json.loads(path.read_text(encoding="utf-8"))
print("Staged and parsed command/ISA catalogues:", len(list(root.iterdir())))
PY_CATALOG_GATE
# ------------------------------------------------------------- rootfs copy
log "staging rootfs"
rm -rf "$WORK"; mkdir -p "$WORK"
# cp -a keeps ownership/modes and is markedly faster than a tar pipe on this tree;
# device nodes are rebuilt empty because CAP_MKNOD is unavailable in the builder.
cp -a "$BASE/." "$WORK/" 2>/dev/null || true
rm -rf "$WORK"/dev "$WORK"/proc "$WORK"/sys "$WORK"/run
mkdir -p "$WORK"/dev "$WORK"/proc "$WORK"/sys "$WORK"/run "$WORK"/tmp "$WORK"/mnt "$WORK"/media

# ------------------------------------------------------------- payload
log "staging payload"
PAY="$WORK/opt/aurora"
rm -rf "$PAY"; mkdir -p "$PAY/wallpapers"
# Rescan the exact target rootfs, then build only missing providers from
# upstream source recipes. Missing providers without real recipes fail closed.
chroot "$WORK" /bin/bash -s <<'PROVIDER_SCAN'
set -euo pipefail
mkdir -p /usr/share/chimera/aurora
: > /usr/share/chimera/aurora/terminal-shell-provider-status.tsv
for item in \
  "xterm:xterm" "gnome-console:kgx" "gnome-terminal:gnome-terminal" \
  "blackbox-terminal:blackbox" "konsole:konsole" "ptyxis:ptyxis" \
  "xfce4-terminal:xfce4-terminal" "foot:foot" "kitty:kitty" \
  "alacritty:alacritty" "wezterm:wezterm" "ghostty:ghostty" "contour:contour" \
  "terminator:terminator" "tilix:tilix" "mate-terminal:mate-terminal" \
  "qterminal:qterminal" "sakura:sakura" "terminology:terminology" "lxterminal:lxterminal" \
  "bash:bash" "zsh:zsh" "fish:fish" "dash:dash" "mksh:mksh" \
  "yash:yash" "elvish:elvish" "nushell:nu"; do
  id="${item%%:*}"
  binary="${item#*:}"
  if path="$(command -v "$binary" 2>/dev/null)" && [ -n "$path" ]; then
    printf '%s\tprovider-present\t%s\n' "$id" "$path" >> /usr/share/chimera/aurora/terminal-shell-provider-status.tsv
  else
    printf '%s\tunavailable\t%s\n' "$id" "$binary" >> /usr/share/chimera/aurora/terminal-shell-provider-status.tsv
  fi
done
PROVIDER_SCAN
install -d "$WORK/usr/share/chimera/aurora/terminals" "$WORK/usr/share/chimera/aurora/shells"
install -m 0644 "$REPO_DIR/aurora/terminals/registry.json" "$WORK/usr/share/chimera/aurora/terminals/registry.json"
install -m 0644 "$REPO_DIR/aurora/shells/registry.json" "$WORK/usr/share/chimera/aurora/shells/registry.json"
PROVIDER_STATUS="$WORK/usr/share/chimera/aurora/terminal-shell-provider-status.tsv"
SOURCE_REQUIRED="$WORK/usr/share/chimera/aurora/terminal-shell-source-required.tsv"
python3 - "$PROVIDER_STATUS" "$SOURCE_REQUIRED" <<'PY_SOURCE_REQUIRED'
import pathlib, sys
status, missing = map(pathlib.Path, sys.argv[1:])
source_recipes = {"bash", "zsh", "fish", "dash", "mksh", "yash", "elvish", "nushell",
                  "alacritty", "foot", "blackbox-terminal", "wezterm", "ghostty", "contour"}
rows = []
for line in status.read_text(encoding="utf-8").splitlines():
    fields = line.split("\t")
    if len(fields) >= 3 and fields[1] == "unavailable" and fields[0] in source_recipes:
        rows.append("|".join((fields[0], fields[2], "distribution-provider-unavailable-source-build-required")))
missing.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")
print("terminal/shell source builds required:", len(rows))
PY_SOURCE_REQUIRED
if [[ -s "$SOURCE_REQUIRED" ]]; then
  bash "$HERE/lib/build-terminal-shell-sources.sh" "$WORK" "$BUILD/terminal-shell-source-build"
fi
python3 "$HERE/lib/verify-terminal-shell-providers.py" "$REPO_DIR" "$WORK" "$PAY"

cp -a "$REPO_DIR/$DESKTOP_COPY" "$PAY/desktop"
[ "$ED" = "octavian" ] && cp -a "$REPO_DIR/apps" "$PAY/apps"

# Aurora desktop shell (multi-profile window manager) is staged for every edition.
if [ -d "$REPO_DIR/desktop/aurora-shell" ]; then
  mkdir -p "$PAY/desktop"
  cp -a "$REPO_DIR/desktop/aurora-shell" "$PAY/desktop/aurora-shell"
fi

python3 - "$ART" "$PAY" <<'PY'
import json, os, subprocess, sys
src, pay = sys.argv[1], sys.argv[2]
manifest = json.load(open(os.path.join(src, "manifest.json")))
out = []
for item in manifest:
    dst = os.path.join(pay, "wallpapers", item["file"])
    subprocess.run(["convert", os.path.join(src, item["file"]),
                    "-resize", "2560x2560>", "-strip", "-quality", "88", dst], check=True)
    out.append({"name": item["name"], "file": item["file"], "url": item["file"],
                "source": item.get("source", "")})
json.dump(out, open(os.path.join(pay, "wallpapers", "index.json"), "w"), indent=1)
print("wallpapers:", len(out))
PY

# verbatim source snapshot for provenance (excluding build output)
mkdir -p "$PAY/repo"
tar -C "$REPO_DIR" --exclude=./.git --exclude=./live-image/.build -cf - . 2>/dev/null \
  | tar -C "$PAY/repo" -xf - 2>/dev/null || true

# Stage every repository-owned application catalog for offline discovery.
# Catalog-only upstream references remain distinct from installed executables.
mkdir -p "$PAY/app-catalogs" "$PAY/apps/native/aurora"
stage_catalog() {
  local rel="$1"
  if [ -f "$REPO_DIR/$rel" ]; then
    mkdir -p "$PAY/app-catalogs/$(dirname "$rel")"
    cp -f "$REPO_DIR/$rel" "$PAY/app-catalogs/$rel"
  fi
}
for rel in \
  applications/catalog.json \
  desktop/optional_apps_catalog.json \
  appcenter/catalog/apps.json \
  appcenter/catalog/external-integrations.json \
  iso/manifests/application-catalog.txt \
  apps/desktop-application-catalog.json; do
  stage_catalog "$rel"
done
if [ "$ED" = "octavian" ]; then
  for rel in \
    vendor/chimera-ii-os/source/applications/catalog.json \
    vendor/chimera-ii-os/source/desktop/optional_apps_catalog.json \
    vendor/chimera-ii-os/source/appcenter/catalog/apps.json \
    vendor/chimera-ii-os/source/appcenter/catalog/external-integrations.json \
    vendor/chimera-ii-os/source/iso/manifests/application-catalog.txt; do
    stage_catalog "$rel"
  done
  if [ -d "$REPO_DIR/vendor/chimera-ii-os/source/desktop/aurora/apps" ]; then
    cp -a "$REPO_DIR/vendor/chimera-ii-os/source/desktop/aurora/apps/." "$PAY/apps/native/aurora/"
  fi
else
  if [ -d "$REPO_DIR/desktop/aurora/apps" ]; then
    cp -a "$REPO_DIR/desktop/aurora/apps/." "$PAY/apps/native/aurora/"
  fi
  mkdir -p "$PAY/apps/native/aurora/launchers"
  find "$REPO_DIR/desktop/aurora" -maxdepth 1 -type f -name '*.desktop' \
    -exec cp -f {} "$PAY/apps/native/aurora/launchers/" \;
fi
python3 - "$PAY/app-catalogs" "$PAY" "$ED" <<'PY'
import json, pathlib, sys
catalog_root, payload, edition = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
files = sorted(str(p.relative_to(catalog_root)) for p in catalog_root.rglob("*") if p.is_file())
manifest = {
    "schema": "aurora-offline-application-bundle-v1",
    "edition": edition,
    "catalog_files": files,
    "native_app_source": "apps/native/aurora",
    "source_snapshot": "repo",
    "policy": "Catalog references are not claims of installation or runtime compatibility. First-party source is bundled; third-party packages remain subject to provider, license, and compatibility checks."
}
(payload / "application-bundle.json").write_text(json.dumps(manifest, indent=2) + "\n")
print("application catalogs:", len(files), "first-party source:", manifest["native_app_source"])
PY

if [ "${ENTRY#desktop/aurora-shell/}" = "$ENTRY" ]; then
  if [ "${ENTRY#desktop/aurora-shell/}" = "$ENTRY" ]; then
    python3 "$HERE/lib/patch_html.py" "$PAY/$ENTRY" "$PAY" wp01.jpg
  fi
fi

cat > "$PAY/PROJECT.md" <<EOF
# $TITLE live image payload

- Upstream: $REPO_URL
- Branch: $BRANCH
- Commit: $COMMIT
- Build date: $VERSION (UTC)
- Volume label: $VOLID

\`desktop/\` is the project's own HTML desktop, rendered fullscreen by the Aurora kiosk
shell (WebKit2GTK). \`wallpapers/\` holds the artwork shipped with this build, wired into
every page's background picker. \`repo/\` is a verbatim snapshot of the source tree.

The image boots a Linux kernel. Openbox manages the Aurora kiosk fullscreen state.
Offline application catalogs and first-party application sources are staged under
app-catalogs/ and apps/native/; catalog-only upstream entries are not misrepresented
as installed applications. The native Spit Fire/Koronos kernel remains a separate
release track until its userspace handoff is verified.
EOF

cat > "$PAY/README.txt" <<EOF
$TITLE live image — $VERSION
===============================
Desktop : $ENTRY (fullscreen kiosk)
Keys    : Ctrl+Q quit kiosk · Ctrl+R reload · Ctrl+Alt+F2 text console
Console : login live / live (passwordless sudo)
Menu    : "Classic X session" boots openbox + xterm
Koronos : experimental native Live console, non-writing Installer ABI probe, Recovery ABI probe
Timeout : GRUB/Jasper/Gates menus wait 300 seconds before the configured default
Artwork : /opt/aurora/wallpapers and /usr/share/backgrounds/$SHORT
Icons   : /opt/aurora/desktop/aurora-icons and /opt/aurora/desktop/app-icons
Apps    : /opt/aurora/app-catalogs and /opt/aurora/apps/native
Source  : $REPO_URL
EOF

# ------------------------------------------------------------- system config
log "system configuration"
install -Dm755 "$HERE/lib/aurora-kiosk.py" "$WORK/usr/local/bin/aurora-kiosk.py"

# Linux-style userspace: systemd units, sysusers/tmpfiles, D-Bus policy, helpers.
if [ -d "$REPO_DIR/userspace" ]; then
  make -C "$REPO_DIR/userspace" install DESTDIR="$WORK" >/dev/null
  echo "  userspace units installed (aurora-shell.target, jasper/gates/aurora targets)"
fi
install -d "$WORK/etc/aurora"
printf 'AURORA_DESKTOP_URI=file:///opt/aurora/%s\n' "$ENTRY" > "$WORK/etc/aurora/session.conf"
printf '%s\n' "${PROFILE:-aurora}" > "$WORK/etc/aurora/profile"

printf '#!/bin/sh\nexec /usr/local/bin/aurora-session\n' > "$WORK/etc/xinitrc"
chmod 755 "$WORK/etc/xinitrc"

chroot "$WORK" /bin/bash -c "
  set -e
  id live >/dev/null 2>&1 || useradd -m -u 1000 -s /bin/bash -G sudo,video,audio,input live
  echo 'live:live' | chpasswd
  echo 'root:live' | chpasswd
"
echo 'live ALL=(ALL) NOPASSWD:ALL' > "$WORK/etc/sudoers.d/90-live"
chmod 440 "$WORK/etc/sudoers.d/90-live"

cp "$WORK/etc/xinitrc" "$WORK/home/live/.xinitrc"
cat > "$WORK/home/live/.bash_profile" <<'EOF'
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
  exec startx
fi
EOF
chown 1000:1000 "$WORK/home/live/.xinitrc" "$WORK/home/live/.bash_profile"

install -d "$WORK/etc/systemd/system/getty@tty1.service.d"
printf '[Service]\nExecStart=\nExecStart=-/sbin/agetty --autologin live --noclear %%I $TERM\nType=simple\n' \
  > "$WORK/etc/systemd/system/getty@tty1.service.d/autologin.conf"

cat > "$WORK/etc/os-release" <<EOF
PRETTY_NAME="$TITLE $VERSION (live)"
NAME="$TITLE"
VERSION="$VERSION"
ID=$SHORT
VERSION_ID=$VERSION
HOME_URL="$REPO_URL"
EOF
cat > "$WORK/etc/issue" <<EOF

  $TITLE $VERSION  ·  live image (x86_64)
  $REPO_URL @ $COMMIT

EOF

echo "$SHORT" > "$WORK/etc/hostname"
printf '127.0.0.1 localhost\n127.0.1.1 %s\n::1 localhost ip6-localhost ip6-loopback\n' "$SHORT" > "$WORK/etc/hosts"

ln -sfn /lib/systemd/system/multi-user.target "$WORK/etc/systemd/system/default.target"
mkdir -p "$WORK/etc/systemd/network" \
         "$WORK/etc/systemd/system/multi-user.target.wants" \
         "$WORK/etc/systemd/system/sockets.target.wants"
printf '[Match]\nName=e*\n[Network]\nDHCP=yes\n' > "$WORK/etc/systemd/network/20-wired.network"
ln -sfn /lib/systemd/system/systemd-networkd.service \
  "$WORK/etc/systemd/system/multi-user.target.wants/systemd-networkd.service"
ln -sfn /lib/systemd/system/systemd-networkd.socket \
  "$WORK/etc/systemd/system/sockets.target.wants/systemd-networkd.socket"

mkdir -p "$WORK/usr/share/backgrounds/$SHORT"
cp -a "$PAY/wallpapers/." "$WORK/usr/share/backgrounds/$SHORT/"

# Export every source-backed Aurora SVG icon and every app-* symbol from the
# original 133-icon artwork sprite. The source/manifest match is strict: no
# empty themes, guessed filenames or missing-symbol placeholders are emitted.
ICON_SOURCE="$COMMAND_SOURCE/desktop/aurora/icons/chimera_icons.cpp"
ICON_CATALOG="$COMMAND_SOURCE/desktop/aurora/icons/icon_theme.json"
ICON_THEME="$WORK/usr/share/icons/chimera-aurora"
ICON_ASSETS="$PAY/desktop/aurora-icons"
if [[ ! -s "$ICON_SOURCE" || ! -s "$ICON_CATALOG" ]]; then
  echo "ERROR: Aurora SVG source or icon catalogue is missing." >&2
  exit 2
fi
python3 "$HERE/lib/export-aurora-icons.py" --source "$ICON_SOURCE" --catalog "$ICON_CATALOG" --output "$ICON_THEME"
test -s "$ICON_THEME/manifest.json"
mkdir -p "$ICON_ASSETS"
cp -a "$ICON_THEME/." "$ICON_ASSETS/"
install -d "$WORK/etc/gtk-3.0"
cat > "$WORK/etc/gtk-3.0/settings.ini" <<'GTK_ICONS'
[Settings]
gtk-icon-theme-name=chimera-aurora
GTK_ICONS

APP_ICON_SOURCE="$COMMAND_SOURCE/desktop/app-icons"
APP_ICON_THEME="$WORK/usr/share/icons/hicolor/scalable/apps"
APP_ICON_ASSETS="$PAY/desktop/app-icons"
if [[ ! -s "$APP_ICON_SOURCE/catalog.svg" || ! -s "$APP_ICON_SOURCE/manifest.json" ]]; then
  echo "ERROR: original Aurora app-icon sprite or manifest is missing." >&2
  exit 2
fi
mkdir -p "$APP_ICON_THEME" "$APP_ICON_ASSETS/icons"
cp -f "$APP_ICON_SOURCE/catalog.svg" "$APP_ICON_ASSETS/catalog.svg"
cp -f "$APP_ICON_SOURCE/manifest.json" "$APP_ICON_ASSETS/manifest.json"
python3 "$HERE/lib/export-app-icon-theme.py" \
  --sprite "$APP_ICON_SOURCE/catalog.svg" \
  --manifest "$APP_ICON_SOURCE/manifest.json" \
  --output "$APP_ICON_THEME"
cp -f "$APP_ICON_THEME"/chimera-*.svg "$APP_ICON_ASSETS/icons/"
cp -f "$APP_ICON_THEME/manifest.json" "$APP_ICON_ASSETS/export-manifest.json"
cat > "$WORK/usr/share/icons/hicolor/index.theme" <<'HICOLOR'
[Icon Theme]
Name=hicolor
Comment=Fallback theme with all exported Aurora app artwork
Directories=scalable/apps
[scalable/apps]
Size=64
Type=Scalable
MinSize=16
MaxSize=256
HICOLOR
python3 - "$ICON_THEME/manifest.json" "$APP_ICON_THEME/manifest.json" <<'PY_ICON_GATE'
import json, pathlib, sys
aurora, apps = (json.loads(pathlib.Path(p).read_text(encoding="utf-8")) for p in sys.argv[1:])
if aurora.get("count") != len(aurora.get("icons", [])) or not aurora.get("count"):
    raise SystemExit("Aurora icon theme export is incomplete")
if apps.get("count") != len(apps.get("icons", [])) or not apps.get("count"):
    raise SystemExit("app artwork export is incomplete")
print(f"Verified {aurora['count']} Aurora UI icons and {apps['count']} app artwork icons")
PY_ICON_GATE

printf 'MODULES=most\nCOMPRESS=gzip\n' > "$WORK/etc/initramfs-tools/conf.d/live.conf"
mount_chroot "$WORK"
chroot "$WORK" /bin/bash -c "update-initramfs -u -k all" >/dev/null
umount_chroot "$WORK"

# ------------------------------------------------------------- shrink
# Compile every SDK/toolchain project we can and ship the honest report.
if [ -x "$REPO_DIR/tools/build-sdks.sh" ]; then
  log "sdk build"
  mkdir -p "$PAY/reports"
  bash "$REPO_DIR/tools/build-sdks.sh" --out "$PAY/reports/sdk-build-report.json" \
    --max 12 --timeout 180 || true
fi

log "trimming"
rm -rf "$WORK"/usr/share/doc/* "$WORK"/usr/share/man/* "$WORK"/usr/share/info/* 2>/dev/null || true
rm -rf "$WORK"/usr/share/fonts/truetype/noto "$WORK"/usr/share/fonts/opentype/noto* 2>/dev/null || true
find "$WORK/usr/share/locale" -mindepth 1 -maxdepth 1 -type d ! -name 'en*' -exec rm -rf {} + 2>/dev/null || true
rm -rf "$WORK"/usr/share/i18n/locales/* 2>/dev/null || true
rm -rf "$WORK"/var/log/* "$WORK"/var/cache/* "$WORK"/tmp/* "$WORK"/usr/lib/debug 2>/dev/null || true

# ------------------------------------------------------------- squashfs + ISO
log "squashfs"
mkdir -p "$ISODIR/live" "$OUT"
rm -f "$ISODIR/live/filesystem.squashfs"
mksquashfs "$WORK" "$ISODIR/live/filesystem.squashfs" \
  -comp xz -Xbcj x86 -b 1M -noappend -processors "$JOBS"

log "boot files"
cp "$WORK"/boot/vmlinuz-* "$ISODIR/live/vmlinuz"
cp "$WORK"/boot/initrd.img-* "$ISODIR/live/initrd.img"
mkdir -p "$ISODIR/boot/grub"
convert "$ART/wp03.jpg" -resize 1920x1080^ -gravity center -extent 1920x1080 \
  -strip -quality 90 "$ISODIR/boot/grub/background.jpg"

cat > "$ISODIR/boot/grub/grub.cfg" <<EOF
set default=0
# Wait for an explicit choice: a 5-minute countdown in full menu style, so the
# Jasper/Gates/profile entries are never skipped by an impatient default.
set timeout=300
set timeout_style=menu
insmod all_video
insmod gfxterm
insmod png
insmod jpeg
insmod font
set gfxmode=1920x1080,1280x1024,1024x768,auto
set gfxpayload=keep
terminal_output gfxterm
if [ -f /boot/grub/background.jpg ]; then background_image /boot/grub/background.jpg; fi

menuentry "$TITLE $VERSION — Live desktop" {
  linux /live/vmlinuz boot=live components hostname=$SHORT username=live console=tty0 console=ttyS0,115200n8 quiet loglevel=3
  initrd /live/initrd.img
}
menuentry "$TITLE $VERSION — Jasper desktop (Windows 12 style)" {
  linux /live/vmlinuz boot=live components hostname=$SHORT username=live aurora.profile=jasper console=tty0 console=ttyS0,115200n8 quiet loglevel=3
  initrd /live/initrd.img
}
menuentry "$TITLE $VERSION — Gates desktop (macOS style)" {
  linux /live/vmlinuz boot=live components hostname=$SHORT username=live aurora.profile=gates console=tty0 console=ttyS0,115200n8 quiet loglevel=3
  initrd /live/initrd.img
}
menuentry "$TITLE $VERSION — Aurora desktop (Linux 7.x style)" {
  linux /live/vmlinuz boot=live components hostname=$SHORT username=live aurora.profile=aurora console=tty0 console=ttyS0,115200n8 quiet loglevel=3
  initrd /live/initrd.img
}
menuentry "$TITLE $VERSION — Classic X session (openbox)" {
  linux /live/vmlinuz boot=live components hostname=$SHORT username=live session=classic console=tty0 console=ttyS0,115200n8 quiet loglevel=3
  initrd /live/initrd.img
}
menuentry "$TITLE $VERSION — Safe graphics (nomodeset)" {
  linux /live/vmlinuz boot=live components hostname=$SHORT username=live nomodeset console=tty0 console=ttyS0,115200n8 quiet loglevel=3
  initrd /live/initrd.img
}
menuentry "$TITLE $VERSION — Verbose boot" {
  linux /live/vmlinuz boot=live components hostname=$SHORT username=live console=tty0 console=ttyS0,115200n8
  initrd /live/initrd.img
}
menuentry "Reboot" { reboot }
menuentry "Power off" { halt }
EOF

# Build and stage the actual Koronos kernel plus separate Live, Installer
# and Recovery ring-3 target ELFs and their matching initramfs/media payloads.
# These are ring-3 text/ABI targets: graphical Live, disk-writing installation
# and the recovery-shell handoff remain separate, explicitly gated work.
log "Koronos kernel and native target payloads"
for tool in nasm gcc g++ ld readelf cpio gzip busybox file; do
  command -v "$tool" >/dev/null 2>&1 || { echo "missing required Koronos build tool: $tool" >&2; exit 2; }
done
if ! file "$(command -v busybox)" | grep -qi "statically linked"; then
  echo "Koronos initramfs requires a statically linked BusyBox (install busybox-static)." >&2
  exit 2
fi
(
  cd "$COMMAND_SOURCE"
  bash kernel/build-koronos.sh
)
CHIMERA_BUILD_DIR="$COMMAND_SOURCE/build" \
CHIMERA_LIVE_BOOT_DIR="$ISODIR" \
  bash "$COMMAND_SOURCE/tools/build-live-boot-binaries.sh"
bash "$COMMAND_SOURCE/tools/chimera-stage-installer-media.sh" "$ISODIR"

for required in \
  "$ISODIR/boot/koronos/koronos.elf" \
  "$ISODIR/boot/targets/target-init-live.elf" \
  "$ISODIR/boot/targets/target-init-installer.elf" \
  "$ISODIR/boot/targets/target-init-recovery.elf" \
  "$ISODIR/boot/live/chimera-live-initramfs.img" \
  "$ISODIR/boot/recovery/chimera-recovery-initramfs.img" \
  "$ISODIR/install/installer/installation.img"; do
  test -s "$required" || { echo "missing native Koronos ISO payload: $required" >&2; exit 2; }
done

# Keep the Linux-hosted Aurora desktop as the default until the Koronos-native
# graphical session passes its own runtime/interaction gates. Offer the three
# real Koronos ring-3 targets explicitly; never label a console probe as a GUI.
python3 - "$ISODIR/boot/grub/grub.cfg" <<'PY_KORONOS_MENU'
from pathlib import Path
import sys
p = Path(sys.argv[1])
text = p.read_text(encoding="utf-8")
if "insmod multiboot2" not in text:
    text = text.replace("insmod all_video", "insmod all_video\ninsmod multiboot2", 1)
text += """
menuentry "OctavianOS — Koronos Native Live Console (experimental)" --id koronos-live {
  multiboot2 /boot/koronos/koronos.elf
  module2 /boot/targets/target-init-live.elf chimera-user-init-elf target=live
  module2 /boot/live/chimera-live-initramfs.img chimera-live-initramfs
  module2 /boot/live/live-manifest.json chimera-live-manifest
  boot
}
menuentry "OctavianOS — Koronos Native Installer Console (non-writing)" --id koronos-installer {
  multiboot2 /boot/koronos/koronos.elf
  module2 /boot/targets/target-init-installer.elf chimera-user-init-elf target=installer
  module2 /install/installer/installation.img chimera-installation-image
  module2 /install/installer/installation-manifest.json chimera-installation-manifest
  module2 /install/installer/installer-contract.json chimera-installer-contract
  module2 /install/installer/installation_phases.json chimera-install-phases
  module2 /install/installer/installer_profiles.json chimera-installer-profiles
  boot
}
menuentry "OctavianOS — Koronos Native Recovery ABI Probe (repair handoff pending)" --id koronos-recovery {
  multiboot2 /boot/koronos/koronos.elf
  module2 /boot/targets/target-init-recovery.elf chimera-user-init-elf target=recovery
  module2 /boot/recovery/chimera-recovery-initramfs.img chimera-recovery-initramfs
  module2 /boot/recovery/recovery-manifest.json chimera-recovery-manifest
  boot
}
"""
p.write_text(text, encoding="utf-8")
PY_KORONOS_MENU

log "iso"
rm -f "$OUT/$ISO_NAME"

grub-mkrescue --compress=xz -o "$OUT/$ISO_NAME" "$ISODIR" -- -volid "$VOLID"
( cd "$OUT" && sha256sum "$ISO_NAME" > "$ISO_NAME.sha256" )
ls -lh "$OUT/$ISO_NAME"
cat "$OUT/$ISO_NAME.sha256"
