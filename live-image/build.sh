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
HERE="$REPO_DIR/live-image"
BUILD="${BUILD_ROOT:-$HERE/.build}"
BASE="$BUILD/rootfs-base"
WORK="$BUILD/rootfs-$ED"
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
if [ ! -x "$BASE/bin/bash" ] || [ ! -f "$BASE/.packages-installed-v3-macos-sdk" ] || [ "${REBUILD_BASE:-0}" = "1" ]; then
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
if [ ! -f "$BASE/.packages-installed" ]; then
  log "installing shared package set (one-off)"
  mount_chroot "$BASE"
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
      python3 python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1 libgtk-4-dev xvfb g++ make \
      clang clangd llvm lld cmake ninja-build pkg-config gobjc libobjc-13-dev gnustep-make libgnustep-base-dev \
      libgl1 libglx-mesa0 libegl1 libgles2 \
      openbox xterm feh \
      fonts-dejavu-core fonts-liberation2 fonts-noto-core \
      sudo ca-certificates curl wget less nano htop pciutils usbutils file unzip xz-utils \
      iproute2 iputils-ping netbase procps psmisc rsync \
      e2fsprogs dosfstools parted gdisk alsa-utils kmod
    apt-get clean
    rm -rf /var/lib/apt/lists/*
  '
  umount_chroot "$BASE"
  touch "$BASE/.packages-installed-v3-macos-sdk"
fi

# ------------------------------------------------------------- rootfs copy
log "staging rootfs"
rm -rf "$WORK"; mkdir -p "$WORK"
tar -C "$BASE" -cf - --exclude=./proc --exclude=./sys --exclude=./dev --exclude=./run . \
  2>/dev/null | tar -C "$WORK" -xf - 2>/dev/null
mkdir -p "$WORK"/dev "$WORK"/proc "$WORK"/sys "$WORK"/run "$WORK"/tmp "$WORK"/mnt "$WORK"/media

# ------------------------------------------------------------- payload
log "staging payload"
PAY="$WORK/opt/aurora"
rm -rf "$PAY"; mkdir -p "$PAY/wallpapers"
python3 - "$PAY/boot-platform.json" "$ED" <<'PYPLATFORM'
import json, pathlib, sys
path, edition = pathlib.Path(sys.argv[1]), sys.argv[2]
manifest = {
    "schema": "octavian-live-platform-v1",
    "edition": edition,
    "kernel_family": "linux",
    "image_role": "live-desktop",
    "native_koronos": False,
    "installer_target": False,
    "recovery_target": False,
    "acceptance_track": "linux-live-image",
    "note": "This live desktop image is not a native Koronos production ISO."
}
path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
PYPLATFORM
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

# The vendored desktop builder compiles from the source snapshot. The GTK4 shell
# source is maintained at the Octavian repository root, so stage it into the
# vendor build tree explicitly rather than advertising a binary the builder
# cannot produce.
if [ "$ED" = "octavian" ] && [ -s "$PAY/repo/desktop/native/chimera-desktop-shell.cpp" ]; then
  install -D -m 0644 \
    "$PAY/repo/desktop/native/chimera-desktop-shell.cpp" \
    "$PAY/repo/vendor/chimera-ii-os/source/desktop/native/chimera-desktop-shell.cpp"
fi

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
  python3 "$HERE/lib/patch_html.py" "$PAY/$ENTRY" "$PAY" wp01.jpg
fi

cat > "$PAY/PROJECT.md" <<EOF
# $TITLE live image payload

- Upstream: $REPO_URL
- Branch: $BRANCH
- Commit: $COMMIT
- Build date: $VERSION (UTC)
- Volume label: $VOLID
- Platform contract: boot-platform.json (Linux live desktop; not native Koronos)

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
# Local-first AI workspace: stage the same opt-in resource indexer used by Chimera.
# This remains a Linux-kernel live edition; it does not claim native Koronos readiness.
AI_SHARE="$WORK/usr/share/chimera/ai"
install -d "$AI_SHARE" "$WORK/usr/bin" "$WORK/usr/local/bin" "$WORK/usr/share/applications" "$PAY/ai"
install -m 0755 "$REPO_DIR/tools/chimera-ai-workspace.py" "$WORK/usr/bin/chimera-ai-workspace"
install -m 0644 "$REPO_DIR/system/ai/chimera-ai-workspace.json" "$AI_SHARE/chimera-ai-workspace.json"
install -m 0644 "$REPO_DIR/system/ai/README.md" "$AI_SHARE/README.md"
install -m 0755 "$REPO_DIR/desktop/shared/chimera-ai-workspace-launcher.sh" "$WORK/usr/local/bin/chimera-ai-workspace-launcher"
install -m 0644 "$REPO_DIR/desktop/aurora/chimera-ai-workspace.desktop" "$WORK/usr/share/applications/chimera-ai-workspace.desktop"
install -m 0644 "$REPO_DIR/desktop/marine/chimera-ai-workspace.desktop" "$WORK/usr/share/applications/chimera-ai-workspace-marine.desktop"
cp -f "$REPO_DIR/system/ai/chimera-ai-workspace.json" "$PAY/ai/"
cp -f "$REPO_DIR/system/ai/README.md" "$PAY/ai/"
cp -f "$REPO_DIR/tools/chimera-ai-workspace.py" "$PAY/ai/"
python3 -m py_compile "$WORK/usr/bin/chimera-ai-workspace"
python3 -m json.tool "$AI_SHARE/chimera-ai-workspace.json" >/dev/null
python3 "$REPO_DIR/tests/test_chimera_ai_workspace.py"
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
    --max 100 --timeout 180
  python3 -c 'import json,pathlib,sys; p=pathlib.Path(sys.argv[1]); p.is_file() or sys.exit("SDK build report missing"); s=json.loads(p.read_text()).get("summary",{}); print("SDK build summary:",s); sys.exit(1 if int(s.get("failed",0))+int(s.get("timeout",0)) else 0)' "$PAY/reports/sdk-build-report.json"
  # macOS app cross-development: package first-party templates and status only.
  # Proprietary Apple SDK content is never copied into the image.
  if [ -x "$REPO_DIR/tools/build-macos-sdk.sh" ]; then
    bash "$REPO_DIR/tools/build-macos-sdk.sh" "$PAY/reports/macos-sdk-report.json" || true
    install -D -m 0755 "$REPO_DIR/tools/build-macos-sdk.sh" "$WORK/usr/local/lib/octavian/build-macos-sdk.sh"
    install -D -m 0644 "$PAY/reports/macos-sdk-report.json" "$WORK/usr/share/octavian/macos-sdk-report.json"
    if [ -d "$REPO_DIR/sdk/macos" ]; then
      mkdir -p "$PAY/sdk/macos" "$WORK/opt/aurora/sdk/macos"
      cp -a "$REPO_DIR/sdk/macos/." "$PAY/sdk/macos/"
      cp -a "$REPO_DIR/sdk/macos/." "$WORK/opt/aurora/sdk/macos/"
    fi
  fi
fi

# Compile the vendor Chimera/Aurora first-party desktop application set in
# the target live-image userspace, then install the binaries and build manifest.
DESKTOP_REL="vendor/chimera-ii-os/source"
DESKTOP_BUILDER="$PAY/repo/$DESKTOP_REL/tools/build-desktop-binaries.sh"
if [ -s "$DESKTOP_BUILDER" ]; then
  log "compiling native Aurora application binaries in the live rootfs"
  mount_chroot "$WORK"
  chroot "$WORK" /bin/bash -c "CHIMERA_DESKTOP_BUILD_DIR=/var/tmp/chimera-desktop-build bash /opt/aurora/repo/$DESKTOP_REL/tools/build-desktop-binaries.sh"
  umount_chroot "$WORK"
  mkdir -p "$PAY/apps/native/bin" "$PAY/apps/native/objects" "$PAY/apps/native/manifests" "$WORK/usr/local/bin" "$WORK/usr/share/applications"
  DESKTOP_BUILD_ROOT="$WORK/var/tmp/chimera-desktop-build"
  DESKTOP_MANIFEST="$DESKTOP_BUILD_ROOT/manifests/desktop-build-manifest.json"
  desktop_build_blocked() {
    printf 'native_desktop_build=BLOCKED\n' > "$PAY/reports/native-desktop-build.status"
    echo "BLOCKED: $1" >&2
    exit 1
  }
  if [ ! -s "$DESKTOP_MANIFEST" ]; then
    desktop_build_blocked "native desktop builder completed without desktop-build-manifest.json"
  fi
  if [ ! -d "$DESKTOP_BUILD_ROOT/bin" ]; then
    desktop_build_blocked "native desktop builder produced no binary directory"
  fi
  cp -a "$DESKTOP_BUILD_ROOT/bin/." "$PAY/apps/native/bin/"
  cp -a "$DESKTOP_BUILD_ROOT/bin/." "$WORK/usr/local/bin/"
  find "$DESKTOP_BUILD_ROOT" -maxdepth 1 -type f -name "*.o" -exec cp -f {} "$PAY/apps/native/objects/" \; 2>/dev/null || true
  cp -f "$DESKTOP_MANIFEST" "$PAY/apps/native/manifests/"
  python3 - "$DESKTOP_MANIFEST" "$WORK/usr/local/bin" "$WORK/usr/share/applications" <<'PYDESKTOP'
import json, pathlib, sys
manifest_path, binaries, desktop_dir = map(pathlib.Path, sys.argv[1:])
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
for item in manifest.get("native_binaries", []):
    name = pathlib.Path(item).name
    if not (binaries / name).is_file():
        raise SystemExit(f"BLOCKED: manifest binary missing from live rootfs: {name}")
    if name == "chimera-desktop-shell":
        continue
    terminal = name in {"chimera-neural-chat", "voiceconnect", "chm-utf8"}
    title = name.replace("-", " ").replace("_", " ").title()
    if name == "chimera-neural-chat":
        title = "Chimera Neural Chat (prototype)"
    (desktop_dir / ("octavian-built-" + name + ".desktop")).write_text(
        "[Desktop Entry]\nType=Application\nName=" + title +
        "\nComment=First-party desktop application\nExec=/usr/local/bin/" + name +
        "\nTerminal=" + ("true" if terminal else "false") +
        "\nCategories=Utility;Development;\n", encoding="utf-8")
PYDESKTOP
  printf 'native_desktop_build=PASS\n' > "$PAY/reports/native-desktop-build.status"
else
  echo "BLOCKED: required first-party native desktop builder missing: $DESKTOP_BUILDER" >&2
  printf 'native_desktop_build=BLOCKED\\n' > "$PAY/reports/native-desktop-build.status"
  exit 1
fi
# The vendor build-desktop-binaries.sh already compiles and headlessly validates
# the GTK4 shell. Install its two desktop profiles after the binaries are copied.
if [ -x "$WORK/usr/local/bin/chimera-desktop-shell" ]; then
  mkdir -p "$WORK/usr/share/applications"
  cat > "$WORK/usr/share/applications/chimera-aurora-shell.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Chimera Aurora Native Shell
Exec=/usr/local/bin/chimera-desktop-shell --desktop=aurora
Terminal=false
Categories=System;DesktopSettings;
EOF
  cat > "$WORK/usr/share/applications/chimera-marine-shell.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Chimera Marine Native Shell
Exec=/usr/local/bin/chimera-desktop-shell --desktop=marine
Terminal=false
Categories=System;DesktopSettings;
EOF
fi

# Install every repository-provided Aurora/Marine desktop entry beside the compiled app binaries.
for desktop_root in "$PAY/repo/vendor/chimera-ii-os/source/desktop/aurora" "$PAY/repo/vendor/chimera-ii-os/source/desktop/marine"; do
  [ -d "$desktop_root" ] || continue
  while IFS= read -r -d '' desktop_file; do
    rel="${desktop_file#"$PAY/repo/vendor/chimera-ii-os/source/desktop/"}"
    desktop_name="$(printf '%s' "$rel" | tr '/' '-')"
    install -D -m 0644 "$desktop_file" "$WORK/usr/share/applications/chimera-$desktop_name"
  done < <(find "$desktop_root" -type f -name "*.desktop" -print0)
done
# Ship executable products produced by the SDK and first-party application builds.
# Catalog entries alone are not treated as installed applications.
mkdir -p "$PAY/apps/native/bin" "$PAY/sdk" "$PAY/reports"
if [ -d "$REPO_DIR/build/sdk/javac-out" ]; then
  mkdir -p "$PAY/sdk/java-classes" "$WORK/opt/aurora/sdk/java-classes"
  cp -a "$REPO_DIR/build/sdk/javac-out/." "$PAY/sdk/java-classes/"
  cp -a "$REPO_DIR/build/sdk/javac-out/." "$WORK/opt/aurora/sdk/java-classes/"
fi
if [ -d "$REPO_DIR/build/sdk" ]; then
  while IFS= read -r -d '' bin; do
    case "$bin" in *.log|*.tmp|*/CMakeFiles/*) continue;; esac
    rel="${bin#"$REPO_DIR/build/sdk"/}"
    install -D -m 0755 "$bin" "$PAY/apps/native/bin/sdk/$rel"
  done < <(find "$REPO_DIR/build/sdk" -type f -perm /111 -print0 2>/dev/null)
fi
for source in "$REPO_DIR/apps/bin" "$REPO_DIR/desktop/aurora/apps" "$REPO_DIR/desktop/marine/apps"; do
  [ -d "$source" ] || continue
  while IFS= read -r -d '' bin; do
    rel="${bin#"$source"/}"
    install -D -m 0755 "$bin" "$PAY/apps/native/bin/$(basename "$source")/$rel"
  done < <(find "$source" -type f -perm /111 -print0 2>/dev/null)
done
python3 - "$PAY/apps/native/bin" "$PAY/apps/native/binary-manifest.json" <<'PYBIN'
import hashlib, json, pathlib, sys
root, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
items=[]
for path in sorted(root.rglob("*")):
    if path.is_file():
        data=path.read_bytes()
        items.append({"path":path.relative_to(root).as_posix(),"size_bytes":len(data),
                      "sha256":hashlib.sha256(data).hexdigest()})
out.write_text(json.dumps({"schema":"octavian-native-app-bundle-v1",
                           "binaries":items,
                           "policy":"Only executable first-party build outputs are staged; catalog references are not binaries."},
                          indent=2)+"\n")
PYBIN

# Build a local, provenance-tracked JSON knowledge database for desktop retrieval.
# Only repository-local allowlisted text roots are indexed; arbitrary host files,
# credentials and home directories are never crawled.
if [ -s "$REPO_DIR/tools/knowledge/build-json-index.py" ]; then
  log "building local knowledge JSON database"
  mkdir -p "$PAY/knowledge" "$WORK/var/lib/octavian/knowledge" "$WORK/usr/lib/octavian/tools/knowledge" "$WORK/usr/share/octavian"
  python3 "$REPO_DIR/tools/knowledge/build-json-index.py" --out "$PAY/knowledge/knowledge-index.json"
  python3 "$REPO_DIR/tools/knowledge/knowledge-chat.py" --index "$PAY/knowledge/knowledge-index.json" --query "Aurora desktop" --limit 2 >/dev/null
  cp -f "$PAY/knowledge/knowledge-index.json" "$WORK/var/lib/octavian/knowledge/"
  install -m 0755 "$REPO_DIR/tools/knowledge/build-json-index.py" "$WORK/usr/lib/octavian/tools/knowledge/build-json-index.py"
  install -m 0755 "$REPO_DIR/tools/knowledge/knowledge-chat.py" "$WORK/usr/lib/octavian/tools/knowledge/knowledge-chat.py"
  cat > "$WORK/usr/share/octavian/knowledge-runtime.json" <<'EOF'
{
  "schema": "octavian-local-ai-runtime-contract-v1",
  "knowledge_database": "/var/lib/octavian/knowledge/knowledge-index.json",
  "mode": "local-retrieval-index",
  "cnn_inference": "requires separately installed model and runtime",
  "rnn_inference": "requires separately installed model and runtime",
  "llm_inference": "requires separately installed model and runtime",
  "training": false,
  "privacy": "repository-local allowlisted text only; no arbitrary host ingestion"
}
EOF
  mkdir -p "$WORK/usr/share/applications"
  cat > "$WORK/usr/share/applications/octavian-knowledge-chat.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Octavian Knowledge Chat
Comment=Search the local knowledge database with source citations
Exec=xterm -e python3 /usr/lib/octavian/tools/knowledge/knowledge-chat.py --index /var/lib/octavian/knowledge/knowledge-index.json
Terminal=true
Categories=Utility;Education;
EOF
  mkdir -p "$WORK/etc/xdg/autostart"
  cat > "$WORK/etc/xdg/autostart/octavian-knowledge-refresh.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Octavian Knowledge Refresh
Comment=Refresh the bounded local resource index at desktop login
Exec=/usr/bin/python3 /usr/lib/octavian/tools/knowledge/build-json-index.py --out /var/lib/octavian/knowledge/knowledge-index.json --root / --source opt/aurora/repo --source opt/aurora/apps --source usr/share/applications --source usr/local/share
Terminal=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
EOF
  cat > "$WORK/usr/share/applications/octavian-knowledge-index.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Octavian Knowledge Index
Comment=Refresh the local, provenance-tracked knowledge database
Exec=xterm -e python3 /usr/lib/octavian/tools/knowledge/build-json-index.py --out /var/lib/octavian/knowledge/knowledge-index.json --root /opt/aurora/repo
Terminal=true
Categories=Utility;Education;
EOF
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
set timeout=10
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

log "iso"
rm -f "$OUT/$ISO_NAME"
grub-mkrescue --compress=xz -o "$OUT/$ISO_NAME" "$ISODIR" -- -volid "$VOLID"
( cd "$OUT" && sha256sum "$ISO_NAME" > "$ISO_NAME.sha256" )
ls -lh "$OUT/$ISO_NAME"
cat "$OUT/$ISO_NAME.sha256"
