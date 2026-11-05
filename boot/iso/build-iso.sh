#!/usr/bin/env bash
# OctavianOS native ISO builder — Live / Installer / Recovery on Koronos.
#
#   boot/iso/build-iso.sh [output.iso]
#
# Produces a BIOS+UEFI hybrid ISO whose GRUB menu boots the Koronos microkernel
# (Multiboot2) and hands each target its own ring-3 init payload:
#   * chimera-user-init-elf target=live|installer|recovery
# The target init is the production payload from kernel/targets/, not a probe.
#
# Requirements: nasm gcc g++ binutils grub-mkrescue xorriso mtools cpio gzip.
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
VENDOR="$ROOT/vendor/chimera-ii-os/source"
OUT_ISO="${1:-$ROOT/build/native-iso/octavian-os-native-amd64.iso}"
WORK="$ROOT/build/native-iso"
ISO_ROOT="$WORK/iso"
KVER="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo snapshot)"

log() { printf '[native-iso] %s\n' "$*"; }

mkdir -p "$WORK"

for tool in grub-mkrescue xorriso nasm gcc ld cpio; do
  command -v "$tool" >/dev/null || { echo "ERROR: missing build tool: $tool" >&2; exit 2; }
done

log "1/6 building Koronos + ring-3 target payloads"
bash "$VENDOR/kernel/build-koronos.sh" >"$WORK/kernel-build.log" 2>&1 || {
  echo "ERROR: kernel build failed; see $WORK/kernel-build.log" >&2; exit 2; }
KELF="$VENDOR/build/koronos/x86_64/koronos.elf"
test -s "$KELF"
grub-file --is-x86-multiboot2 "$KELF" || { echo "ERROR: koronos.elf is not Multiboot2" >&2; exit 2; }
for t in live installer recovery; do
  test -s "$VENDOR/build/koronos/x86_64/target-init-$t.elf" || {
    echo "ERROR: production init for $t was not built" >&2; exit 2; }
done

log "2/6 building live/recovery initramfs"
bash "$VENDOR/tools/build-live-boot-binaries.sh" >"$WORK/live-boot-build.log" 2>&1 || {
  echo "ERROR: initramfs build failed; see $WORK/live-boot-build.log" >&2; exit 2; }
LB="$VENDOR/build/live-boot"

log "3/6 assembling ISO tree"
rm -rf "$ISO_ROOT"
mkdir -p "$ISO_ROOT/boot/grub" "$ISO_ROOT/boot/koronos" "$ISO_ROOT/boot/targets" \
         "$ISO_ROOT/boot/live" "$ISO_ROOT/boot/recovery" "$ISO_ROOT/boot/visual" \
         "$ISO_ROOT/install/installer"
cp -f "$KELF" "$ISO_ROOT/boot/koronos/koronos.elf"
for t in live installer recovery; do
  cp -f "$VENDOR/build/koronos/x86_64/target-init-$t.elf" "$ISO_ROOT/boot/targets/target-init-$t.elf"
done
if [ -d "$LB/boot/live" ]; then cp -f "$LB/boot/live/"* "$ISO_ROOT/boot/live/" 2>/dev/null || true; fi
if [ -d "$LB/boot/recovery" ]; then cp -f "$LB/boot/recovery/"* "$ISO_ROOT/boot/recovery/" 2>/dev/null || true; fi
[ -f "$ROOT/boot/live/desktop-sessions.json" ] && cp -f "$ROOT/boot/live/desktop-sessions.json" "$ISO_ROOT/boot/live/"
for f in installation.img installation-manifest.json installer-contract.json installation_phases.json installer_profiles.json; do
  src="$ROOT/build/live-boot/boot/install/$f"
  [ -f "$src" ] || src="$LB/boot/install/$f"
  [ -f "$src" ] && cp -f "$src" "$ISO_ROOT/install/installer/$f"
done

log "3b/6 staging the AI knowledge database"
KB="$ROOT/config/ai/knowledge-db.json"
test -s "$KB" || { echo "ERROR: knowledge database missing: $KB" >&2; exit 2; }
mkdir -p "$ISO_ROOT/boot/ai"
cp -f "$KB" "$ISO_ROOT/boot/ai/knowledge-db.json"
python3 "$ROOT/tools/ai/knowledge_db.py" validate --db "$ISO_ROOT/boot/ai/knowledge-db.json" >/dev/null || {
  echo "ERROR: staged knowledge database failed validation" >&2; exit 2; }

log "4/6 staging boot artwork"
python3 - "$ROOT" "$ISO_ROOT" <<'PY' || true
import os, subprocess, sys
root, iso = sys.argv[1], sys.argv[2]
assets = [
    ("desktop/aurora/assets/octavian-octopus-background.svg", "boot/grub/octavian-octopus-background.png"),
    ("boot/splash/octavian-octopus-background.svg", "boot/grub/octavian-octopus-background.png"),
]
for src, dst in assets:
    s = os.path.join(root, src)
    d = os.path.join(iso, dst)
    if os.path.exists(s):
        os.makedirs(os.path.dirname(d), exist_ok=True)
        try:
            subprocess.run([sys.executable, "-c", "import cairosvg,sys;cairosvg.svg2png(url=sys.argv[1],write_to=sys.argv[2],output_width=1920)", s, d], check=True)
            break
        except Exception:
            continue
PY
if [ ! -f "$ISO_ROOT/boot/grub/octavian-octopus-background.png" ]; then
  # Fall back to the repository wallpaper so the GRUB menu always has art.
  if command -v convert >/dev/null; then
    convert "$ROOT/live-image/artwork/wp01.jpg" -resize 1920x1080^ -gravity center -extent 1920x1080 -strip \
      "$ISO_ROOT/boot/grub/octavian-octopus-background.png" 2>/dev/null || true
  fi
fi

cp -f "$ROOT/boot/iso/grub.cfg" "$ISO_ROOT/boot/grub/grub.cfg"
for cfg in boot/jasper/live.cfg boot/jasper/install.cfg boot/jasper/recovery.cfg boot/jasper/diagnostics.cfg \
           boot/jasper/safe.cfg boot/jasper/retro.cfg boot/jasper/jasper.cfg boot/installation/menu.cfg \
           boot/spitfire/spitfire-menu.cfg; do
  [ -f "$ROOT/$cfg" ] || continue
  mkdir -p "$ISO_ROOT/$(dirname "$cfg")"
  cp -f "$ROOT/$cfg" "$ISO_ROOT/$cfg"
done

log "5/6 validating menu contract"
grep -q "ai-knowledge-db" "$ISO_ROOT/boot/grub/grub.cfg" || { echo "ERROR: no knowledge-db module in menu" >&2; exit 2; }
for t in live installer recovery; do
  grep -q "target-init-$t.elf chimera-user-init-elf target=$t" "$ISO_ROOT/boot/grub/grub.cfg" \
    || grep -rq "target-init-$t.elf chimera-user-init-elf target=$t" "$ISO_ROOT/boot/jasper" "$ISO_ROOT/boot/installation" 2>/dev/null || {
      echo "ERROR: no ring-3 init module staged in the menu graph for target=$t" >&2; exit 2; }
done
test -s "$ISO_ROOT/boot/live/chimera-live-initramfs.img" || { echo "ERROR: live initramfs missing" >&2; exit 2; }
test -s "$ISO_ROOT/boot/recovery/chimera-recovery-initramfs.img" || { echo "ERROR: recovery initramfs missing" >&2; exit 2; }

log "6/6 building hybrid BIOS+UEFI ISO"
mkdir -p "$(dirname "$OUT_ISO")"
rm -f "$OUT_ISO"
grub-mkrescue -o "$OUT_ISO" "$ISO_ROOT" >"$WORK/grub-mkrescue.log" 2>&1 || {
  echo "ERROR: grub-mkrescue failed; see $WORK/grub-mkrescue.log" >&2; exit 2; }
sha256sum "$OUT_ISO" | tee "$OUT_ISO.sha256"
xorriso -indev "$OUT_ISO" -report_el_torito plain -report_system_area plain > "$OUT_ISO.boot-report.txt" 2>&1 || true
printf 'ISO      : %s\nCommit   : %s\nKernel   : %s\nTargets  : live installer recovery (ring 3)\n' \
  "$OUT_ISO" "$KVER" "$KELF"
