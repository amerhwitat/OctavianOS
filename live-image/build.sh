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
      python3 python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1 \
      libgl1 libglx-mesa0 libegl1 libgles2 \
      openbox xterm feh \
      fonts-dejavu-core fonts-liberation2 fonts-noto-core \
      sudo ca-certificates curl wget less nano htop pciutils usbutils file unzip xz-utils binutils \
      iproute2 iputils-ping netbase procps psmisc rsync \
      e2fsprogs dosfstools parted gdisk alsa-utils kmod
    # Resolve optional open-source terminals and shells against the actual
    # Debian repository for this rootfs architecture; absent packages remain
    # explicitly unavailable rather than receiving placeholder executables.
    terminal_shell_packages=()
    for package in gnome-console gnome-terminal blackbox-terminal konsole ptyxis xfce4-terminal foot kitty alacritty wezterm ghostty contour terminator tilix mate-terminal qterminal sakura terminology lxterminal zsh fish dash mksh yash elvish nushell; do
      if apt-cache show "$package" >/dev/null 2>&1; then
        terminal_shell_packages+=("$package")
      else
        echo "[TERMINAL-SHELL][UNAVAILABLE] package=$package arch=$(dpkg --print-architecture)"
      fi
    done
    if ((${#terminal_shell_packages[@]} > 0)); then
      apt-get install -y -qq --no-install-recommends "${terminal_shell_packages[@]}"
    fi
    # Install real open-source astronomy applications when the target
    # distribution publishes packages for this architecture. Missing packages
    # are reported explicitly; no launcher or executable placeholder is made.
    astronomy_packages=()
    for package in stellarium kstars xplanet astrometry.net; do
      if apt-cache show "$package" >/dev/null 2>&1; then
        astronomy_packages+=("$package")
      else
        echo "[ASTRONOMY][UNAVAILABLE] package=$package arch=$(dpkg --print-architecture)"
      fi
    done
    if ((${#astronomy_packages[@]} > 0)); then
      apt-get install -y -qq --no-install-recommends "${astronomy_packages[@]}"
    fi
    mkdir -p /usr/share/chimera/aurora
    {
      for item in \
        "xterm:xterm" "gnome-console:kgx" "gnome-terminal:gnome-terminal" \
        "blackbox-terminal:blackbox" "konsole:konsole" "ptyxis:ptyxis" \
        "xfce4-terminal:xfce4-terminal" "foot:foot" "kitty:kitty" \
        "alacritty:alacritty" "wezterm:wezterm" "ghostty:ghostty" "contour:contour" \
        "terminator:terminator" "tilix:tilix" "mate-terminal:mate-terminal" \
        "qterminal:qterminal" "sakura:sakura" "terminology:terminology" "lxterminal:lxterminal" \
        "bash:bash" "zsh:zsh" "fish:fish" "dash:dash" "mksh:mksh" \
        "yash:yash" "elvish:elvish" "nushell:nu"; do
        id="${item%%:*}"; binary="${item#*:}"
        if command -v "$binary" >/dev/null 2>&1; then
          path="$(command -v "$binary")"
          if readelf -h "$path" >/dev/null 2>&1; then
            machine="$(readelf -h "$path" | sed -n 's/^[[:space:]]*Machine:[[:space:]]*//p')"
            printf '%s\tverified-elf\t%s\t%s\n' "$id" "$path" "$machine"
          else
            printf '%s\tprovider-present-non-elf\t%s\n' "$id" "$path"
          fi
        else
          printf '%s\tunavailable\t%s\n' "$id" "$binary"
        fi
      done
    } > /usr/share/chimera/aurora/terminal-shell-provider-status.tsv
    apt-get clean
    rm -rf /var/lib/apt/lists/*
  '
  umount_chroot "$BASE"
  touch "$BASE/.packages-installed"
fi

# ------------------------------------------------------------- rootfs copy
log "staging rootfs"
rm -rf "$WORK"; mkdir -p "$WORK"
# cp -a keeps ownership/modes and is markedly faster than a tar pipe on this tree;
# device nodes are rebuilt empty because CAP_MKNOD is unavailable in the builder.
cp -a "$BASE/." "$WORK/" 2>/dev/null || true
# Re-scan the copied target rootfs, rather than trusting a possibly cached
# base-rootfs report. This makes the provider manifest describe the exact
# filesystem that will be packed into the ISO.
chroot "$WORK" /bin/bash -s <<'PROVIDER_SCAN'
set -euo pipefail
mkdir -p /usr/share/chimera/aurora
: > /usr/share/chimera/aurora/terminal-shell-provider-status.tsv
for item in \
  "xterm:xterm" "gnome-terminal:gnome-terminal" "konsole:konsole" \
  "xfce4-terminal:xfce4-terminal" "foot:foot" "kitty:kitty" \
  "alacritty:alacritty" "wezterm:wezterm" "ghostty:ghostty" \
  "contour:contour" "bash:bash" "zsh:zsh" "fish:fish" \
  "dash:dash" "mksh:mksh" "yash:yash" "elvish:elvish" "nushell:nu"; do
  id="${item%%:*}"
  binary="${item#*:}"
  if path="$(command -v "$binary" 2>/dev/null)" && [ -n "$path" ]; then
    if readelf -h "$path" >/dev/null 2>&1; then
      machine="$(readelf -h "$path" | sed -n 's/^[[:space:]]*Machine:[[:space:]]*//p')"
      printf '%s\tverified-elf\t%s\t%s\n' "$id" "$path" "$machine" \
        >> /usr/share/chimera/aurora/terminal-shell-provider-status.tsv
    else
      printf '%s\tprovider-present-non-elf\t%s\n' "$id" "$path" \
        >> /usr/share/chimera/aurora/terminal-shell-provider-status.tsv
    fi
  else
    printf '%s\tunavailable\t%s\n' "$id" "$binary" \
      >> /usr/share/chimera/aurora/terminal-shell-provider-status.tsv
  fi
done
echo "Target-rootfs provider scan:"
cat /usr/share/chimera/aurora/terminal-shell-provider-status.tsv
PROVIDER_SCAN
# Keep the same terminal/shell catalogue in both live editions, independently
# of which optional provider packages are available on this build architecture.
install -d "$WORK/usr/share/chimera/aurora/terminals" "$WORK/usr/share/chimera/aurora/shells"
install -m 0644 "$REPO_DIR/aurora/terminals/registry.json" "$WORK/usr/share/chimera/aurora/terminals/registry.json"
install -m 0644 "$REPO_DIR/aurora/shells/registry.json" "$WORK/usr/share/chimera/aurora/shells/registry.json"
rm -rf "$WORK"/dev "$WORK"/proc "$WORK"/sys "$WORK"/run
mkdir -p "$WORK"/dev "$WORK"/proc "$WORK"/sys "$WORK"/run "$WORK"/tmp "$WORK"/mnt "$WORK"/media

# ------------------------------------------------------------- payload
log "staging payload"
PAY="$WORK/opt/aurora"
rm -rf "$PAY"; mkdir -p "$PAY/wallpapers"

# Compile the supported missing providers from upstream source; do not let an
# unavailable package silently become a catalogue-only success.
PROVIDER_STATUS="$WORK/usr/share/chimera/aurora/terminal-shell-provider-status.tsv"
SOURCE_REQUIRED="$WORK/usr/share/chimera/aurora/terminal-shell-source-required.tsv"
python3 - "$PROVIDER_STATUS" "$SOURCE_REQUIRED" <<'PY'
import pathlib, sys
status, missing = map(pathlib.Path, sys.argv[1:])
source_recipes = {"bash", "zsh", "fish", "dash", "mksh", "yash", "elvish", "nushell", "alacritty", "foot", "blackbox-terminal", "wezterm", "ghostty", "contour"}
rows = []
if status.is_file():
    for line in status.read_text().splitlines():
        fields = line.split("\t")
        if len(fields) >= 3 and fields[1] == "unavailable" and fields[0] in source_recipes:
            rows.append("|".join((fields[0], fields[2], "distribution-provider-unavailable-source-build-required")))
missing.parent.mkdir(parents=True, exist_ok=True)
missing.write_text("\n".join(rows) + ("\n" if rows else ""))
print("terminal/shell source builds required:", len(rows))
PY
if [ -s "$SOURCE_REQUIRED" ]; then
  bash "$HERE/lib/build-terminal-shell-sources.sh" "$WORK" "$BUILD/terminal-shell-source-build"
fi
python3 - "$REPO_DIR" "$WORK" "$PAY" <<'PY'
import json, pathlib, subprocess, sys
repo, root, payload = map(pathlib.Path, sys.argv[1:])
registries = [repo / "aurora/terminals/registry.json", repo / "aurora/shells/registry.json"]
entries = [entry for path in registries for entry in json.loads(path.read_text())["entries"]]
status_path = root / "usr/share/chimera/aurora/terminal-shell-provider-status.tsv"
statuses = {}
if status_path.is_file():
    for line in status_path.read_text().splitlines():
        fields = line.split("\t")
        if len(fields) >= 3:
            statuses[fields[0]] = {"status": fields[1], "path": fields[2], "machine": fields[3] if len(fields) > 3 else ""}
built_path = root / "usr/share/chimera/aurora/terminal-shell-installed.tsv"
if built_path.is_file():
    for line in built_path.read_text().splitlines():
        fields = line.split("|")
        if len(fields) >= 5 and fields[2] == "source-built":
            statuses[fields[0]] = {"status": "source-built", "path": "/usr/local/bin/" + fields[1], "machine": ""}
arch = subprocess.check_output(["chroot", str(root), "dpkg", "--print-architecture"], text=True).strip()
expected = {"amd64": "Advanced Micro Devices X86-64", "arm64": "AArch64", "armhf": "ARM", "i386": "Intel 80386", "riscv64": "RISC-V", "ppc64el": "PowerPC64", "s390x": "IBM S/390"}.get(arch)
if not expected:
    raise SystemExit(f"unsupported target architecture for provider verification: {arch}")
verified, failures = [], []
for entry in entries:
    ident, binary = entry["id"], entry["binary"]
    item = statuses.get(ident)
    if not item or item["status"] == "unavailable":
        failures.append(f"{ident}: no installed or source-built provider")
        continue
    rel = item["path"]
    path = root / rel.lstrip("/")
    if not path.is_file():
        failures.append(f"{ident}: provider path missing in target rootfs: {rel}")
        continue
    header = subprocess.run(["readelf", "-h", str(path)], text=True, capture_output=True)
    if header.returncode == 0:
        machine = next((line.split(":", 1)[1].strip() for line in header.stdout.splitlines() if "Machine:" in line), "")
        if machine != expected:
            failures.append(f"{ident}: ELF machine {machine!r} does not match {arch}/{expected}")
            continue
        kind = "verified-elf"
    else:
        first = path.open("rb").readline(256).decode("utf-8", "replace").strip()
        if not first.startswith("#!"):
            failures.append(f"{ident}: provider is neither a target ELF nor an executable script")
            continue
        interpreter = first[2:].split()[0]
        if not (root / interpreter.lstrip("/")).exists():
            failures.append(f"{ident}: script interpreter missing: {interpreter}")
            continue
        kind = "verified-script"
    # Execute each provider inside the target rootfs. Shells must execute a
    # command; terminal emulators must successfully report their version.
    # This does not claim that GUI windows were interactively exercised.
    if entry["kind"] == "shell":
        shell_commands = {
            "bash": ["-c", "printf CHIMERA_SHELL_SMOKE"],
            "zsh": ["-c", "printf CHIMERA_SHELL_SMOKE"],
            "fish": ["-c", "printf CHIMERA_SHELL_SMOKE"],
            "dash": ["-c", "printf CHIMERA_SHELL_SMOKE"],
            "mksh": ["-c", "printf CHIMERA_SHELL_SMOKE"],
            "yash": ["-c", "printf CHIMERA_SHELL_SMOKE"],
            "elvish": ["-c", "echo CHIMERA_SHELL_SMOKE"],
            "nu": ["-c", "print CHIMERA_SHELL_SMOKE"],
        }
        args = shell_commands.get(binary, ["--version"])
        expected_output = b"CHIMERA_SHELL_SMOKE"
    else:
        args = ["-version"] if binary == "xterm" else ["--version"]
        expected_output = None
    try:
        probe = subprocess.run(["chroot", str(root), rel, *args],
                                capture_output=True, timeout=15)
        output = probe.stdout + probe.stderr
        if probe.returncode != 0 or (expected_output and expected_output not in output):
            failures.append(f"{ident}: provider execution smoke failed (exit={probe.returncode})")
            continue
    except (OSError, subprocess.TimeoutExpired) as exc:
        failures.append(f"{ident}: provider execution smoke failed: {exc}")
        continue
    verified.append({"id": ident, "binary": binary, "path": rel, "status": kind,
                     "elf_machine": expected if kind == "verified-elf" else None,
                     "runtime_status": "shell-command-smoke-pass" if entry["kind"] == "shell" else "version-smoke-pass"})
if failures:
    raise SystemExit("terminal/shell provider gate failed:\n" + "\n".join(failures))
manifest = {"schema": "octavian-terminal-shell-provider-verification/v1", "target_architecture": arch,
            "required": len(entries), "verified": len(verified), "providers": verified,
            "runtime_launch_smoke": "shell command and terminal --version smoke tests passed; GUI launch/input not tested"}
out = root / "usr/share/chimera/aurora/terminal-shell-provider-verification.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
import shutil
shutil.copy2(out, payload / "terminal-shell-provider-verification.json")
print(f"verified all {len(verified)} terminal/shell providers for {arch}")
PY
cp -a "$REPO_DIR/$DESKTOP_COPY" "$PAY/desktop"

# Export every real SVG icon embedded in the vendored Aurora source into an
# installable icon theme and the desktop's offline asset bundle.
ICON_SOURCE="$REPO_DIR/vendor/chimera-ii-os/source/desktop/aurora/icons/chimera_icons.cpp"
ICON_THEME="$WORK/usr/share/icons/chimera-aurora"
ICON_ASSETS="$PAY/desktop/aurora-shell/assets/icons/generated"
if [ ! -s "$ICON_SOURCE" ]; then
  echo "ERROR: embedded Aurora SVG icon source is missing: $ICON_SOURCE" >&2
  exit 2
fi
ICON_CATALOG="$REPO_DIR/vendor/chimera-ii-os/source/desktop/aurora/icons/icon_theme.json"
if [ ! -s "$ICON_CATALOG" ]; then
  echo "ERROR: Aurora icon catalogue is missing: $ICON_CATALOG" >&2
  exit 2
fi
python3 "$HERE/lib/export-aurora-icons.py" --source "$ICON_SOURCE" --catalog "$ICON_CATALOG" --output "$ICON_THEME"
test -s "$ICON_THEME/manifest.json"
mkdir -p "$ICON_ASSETS"
cp -a "$ICON_THEME/scalable/apps/." "$ICON_ASSETS/"
install -d "$WORK/etc/gtk-3.0"
cat > "$WORK/etc/gtk-3.0/settings.ini" <<'GTK'
[Settings]
gtk-icon-theme-name=chimera-aurora
GTK
echo "  Aurora SVG icons exported and staged: $(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["count"])' "$ICON_THEME/manifest.json")"

# Export the complete 133-symbol original app artwork sprite as real SVG files.
APP_ICON_SOURCE="$REPO_DIR/vendor/chimera-ii-os/source/desktop/app-icons"
APP_ICON_THEME="$WORK/usr/share/icons/hicolor/scalable/apps"
APP_ICON_ASSETS="$PAY/desktop/app-icons"
if [ ! -s "$APP_ICON_SOURCE/catalog.svg" ] || [ ! -s "$APP_ICON_SOURCE/manifest.json" ]; then
  echo "ERROR: complete Aurora app-icon sprite/manifest is missing" >&2
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
echo "  Original Aurora app artwork exported: $(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["count"])' "$APP_ICON_THEME/manifest.json")"

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

# Stage the same vendored command and ISA catalogue data in the hosted edition.
bash "$REPO_DIR/live-image/lib/stage-command-isa-catalogs.sh" \
  "$REPO_DIR/vendor/chimera-ii-os/source" "$PAY"

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

# Native Koronos kernel (vendored Chimera II tree) built with the Linux-style kbuild
# workflow and staged as a multiboot2 diagnostic payload. It never replaces the
# Linux live entries: the microkernel has no verified userspace handoff.
log "koronos kernel"
if [ -f "$REPO_DIR/kernel/Makefile" ] && command -v nasm >/dev/null 2>&1; then
  ( cd "$REPO_DIR" && make -C kernel defconfig all >/tmp/octavian-koronos.log 2>&1 ) || \
    echo "  [warn] Koronos build failed, see /tmp/octavian-koronos.log"
  koronos_elf="$(ls "$REPO_DIR"/vendor/chimera-ii-os/source/build/koronos/x86_64/koronos.elf 2>/dev/null | head -1)"
  if [ -n "$koronos_elf" ] && [ -s "$koronos_elf" ]; then
    install -Dm644 "$koronos_elf" "$ISODIR/boot/koronos/koronos.elf"
    install -Dm644 "$(dirname "$koronos_elf")/System.map" "$ISODIR/boot/koronos/System.map" 2>/dev/null || true
    echo "  staged $(du -h "$koronos_elf" | cut -f1) koronos.elf"
  fi
fi

log "iso"
rm -f "$OUT/$ISO_NAME"
if [ -f "$ISODIR/boot/koronos/koronos.elf" ]; then
  cat >> "$ISODIR/boot/grub/grub.cfg" <<'KORONOS'

menuentry "Koronos native microkernel (diagnostic console — no graphical userspace)" {
  echo "Loading Koronos microkernel (multiboot2)…"
  multiboot2 /boot/koronos/koronos.elf
  boot
}
KORONOS
fi

grub-mkrescue --compress=xz -o "$OUT/$ISO_NAME" "$ISODIR" -- -volid "$VOLID"
( cd "$OUT" && sha256sum "$ISO_NAME" > "$ISO_NAME.sha256" )
ls -lh "$OUT/$ISO_NAME"
cat "$OUT/$ISO_NAME.sha256"
