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
# grub-efi-amd64-bin mtools dosfstools imagemagick python3.
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
if [ ! -f "$BASE/.packages-installed-v2" ]; then
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
      for pkg in bash zsh fish dash mksh yash elvish nushell gnome-terminal konsole xfce4-terminal foot kitty alacritty wezterm ghostty contour; do
        if apt-cache show "$pkg" >/dev/null 2>&1; then
          apt-get install -y -qq --no-install-recommends "$pkg" || echo "[AURORA-TERMINALS] package install failed: $pkg"
        else
          echo "[AURORA-TERMINALS] no Debian package candidate: $pkg"
        fi
      done
    bash /tmp/chimera-install-command-providers.sh
    rm -f /tmp/chimera-install-command-providers.sh
    apt-get clean
    rm -rf /var/lib/apt/lists/*
  '
  umount_chroot "$BASE"
  bash "$REPO_DIR/live-image/verify-terminal-shell-suite.sh" "$BASE" x86_64
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
  touch "$BASE/.packages-installed-v2"
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
python3 - "$CATALOG_DEST" <<'PY_CATALOG_GATE'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
required = ("octavian-command-list.json", "catalog.json", "isa-encoding-registry.json")
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
Artwork : /opt/aurora/wallpapers and /usr/share/backgrounds/$SHORT
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
# These are currently safe native text consoles: graphical Live, disk-writing
# installation and filesystem repair remain separate, explicitly gated work.
log "Koronos kernel and native target payloads"
for tool in nasm gcc g++ ld readelf cpio gzip busybox; do
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
menuentry "OctavianOS — Koronos Native Recovery Console (read-only)" --id koronos-recovery {
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
