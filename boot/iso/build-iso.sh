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

log "3b/6 staging source-attributed AI knowledge and advisory RNN"
AI_DIR="$ISO_ROOT/system/ai"
mkdir -p "$AI_DIR"
python3 "$VENDOR/tools/cognition/knowledge_database.py" validate --database "$VENDOR/data/ai/hardware_systems_knowledge.json"
python3 "$VENDOR/tools/cognition/train_knowledge_rnn.py" \
  --database "$VENDOR/data/ai/hardware_systems_knowledge.json" \
  --output "$AI_DIR/trained-hardware-systems-rnn.json" --epochs "${OCTAVIAN_AI_RNN_EPOCHS:-2}" --hidden 8
cp -f "$VENDOR/data/ai/hardware_systems_knowledge.json" "$AI_DIR/hardware-systems-knowledge.json"
cp -f "$VENDOR/data/ai/hardware_systems_knowledge.schema.json" "$AI_DIR/hardware-systems-knowledge.schema.json"
cp -f "$VENDOR/system/ai/chimera-ai-workspace.json" "$AI_DIR/"
cp -f "$VENDOR/system/ai/README.md" "$AI_DIR/"
cp -f "$VENDOR/tools/chimera-ai-workspace.py" "$AI_DIR/"
cp -f "$VENDOR/tools/cognition/knowledge_database.py" "$AI_DIR/"
cp -f "$VENDOR/tools/cognition/train_knowledge_rnn.py" "$AI_DIR/"
cp -f "$VENDOR/tools/cognition/trainable_rnn_lm.py" "$AI_DIR/"
python3 -m py_compile "$AI_DIR/chimera-ai-workspace.py" "$AI_DIR/knowledge_database.py" "$AI_DIR/train_knowledge_rnn.py" "$AI_DIR/trainable_rnn_lm.py"
python3 -m json.tool "$AI_DIR/hardware-systems-knowledge.json" >/dev/null
python3 -m json.tool "$AI_DIR/hardware-systems-knowledge.schema.json" >/dev/null
python3 -m json.tool "$AI_DIR/trained-hardware-systems-rnn.json" >/dev/null
python3 - "$AI_DIR" <<'PYAI'
import hashlib, json, pathlib, sys
root=pathlib.Path(sys.argv[1])
db=json.loads((root/"hardware-systems-knowledge.json").read_text(encoding="utf-8"))
model=json.loads((root/"trained-hardware-systems-rnn.json").read_text(encoding="utf-8"))
manifest={
 "schema":"OCTAVIAN-AI-PAYLOAD-1",
 "knowledge_database":"system/ai/hardware-systems-knowledge.json",
 "knowledge_schema":"system/ai/hardware-systems-knowledge.schema.json",
 "knowledge_entries":db["entry_count"],
 "knowledge_sources":db["source_count"],
 "knowledge_sha256":hashlib.sha256((root/"hardware-systems-knowledge.json").read_bytes()).hexdigest(),
 "rnn_model":"system/ai/trained-hardware-systems-rnn.json",
 "rnn_corpus_sha256":model.get("metadata",{}).get("corpus_sha256"),
 "rnn_train_sequences":model.get("metadata",{}).get("train_sequences"),
 "rnn_heldout_sequences":model.get("metadata",{}).get("heldout_sequences"),
 "rnn_scope":"small advisory character-level RNN; not an LLM"
}
(root/"ai-payload-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"status":"AI payload staged","entries":db["entry_count"],"sources":db["source_count"]}))
PYAI
python3 -m json.tool "$AI_DIR/ai-payload-manifest.json" >/dev/null

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
# Verify the AI knowledge and model files exist inside the final ISO.
AI_VERIFY="$WORK/ai-payload-verify"
mkdir -p "$AI_VERIFY"
for item in hardware-systems-knowledge.json hardware-systems-knowledge.schema.json trained-hardware-systems-rnn.json ai-payload-manifest.json; do
  xorriso -osirrox on -indev "$OUT_ISO" -extract "/system/ai/$item" "$AI_VERIFY/$item" >/dev/null
  test -s "$AI_VERIFY/$item" || { echo "ERROR: AI ISO payload missing: $item" >&2; exit 2; }
done
python3 -m json.tool "$AI_VERIFY/ai-payload-manifest.json" >/dev/null
printf 'ISO      : %s\nCommit   : %s\nKernel   : %s\nTargets  : live installer recovery (ring 3)\nAI DB    : %s entries / %s sources\n' \
  "$OUT_ISO" "$KVER" "$KELF" \
  "$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["knowledge_entries"])' "$AI_VERIFY/ai-payload-manifest.json")" \
  "$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["knowledge_sources"])' "$AI_VERIFY/ai-payload-manifest.json")"
