#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
SOURCE="$ROOT/vendor/chimera-ii-os/source"
cd "$SOURCE"
smoke=build/qemu-smoke
matrix="$smoke/production-matrix"
mkdir -p "$matrix"
ovmf_code=""
ovmf_vars=""
for pair in "OVMF_CODE_4M.fd:OVMF_VARS_4M.fd" "OVMF_CODE.fd:OVMF_VARS.fd" "edk2-x86_64-code.fd:edk2-x86_64-vars.fd"; do
  code_name="${pair%%:*}"
  vars_name="${pair##*:}"
  code_path="$(find /usr/share/OVMF /usr/share/ovmf /usr/share/qemu \( -type f -o -type l \) -name "$code_name" -print -quit 2>/dev/null || true)"
  vars_path="$(find /usr/share/OVMF /usr/share/ovmf /usr/share/qemu \( -type f -o -type l \) -name "$vars_name" -print -quit 2>/dev/null || true)"
  if [[ -n "$code_path" && -s "$code_path" && -n "$vars_path" && -s "$vars_path" ]]; then
    ovmf_code="$code_path"
    ovmf_vars="$vars_path"
    break
  fi
done
if [[ -z "$ovmf_code" || -z "$ovmf_vars" ]]; then
  echo "ERROR: matching OVMF CODE/VARS pair unavailable; cannot claim six-case coverage." >&2
  dpkg -L ovmf 2>/dev/null | grep -E '\\.(fd|bin)$' || true
  exit 1
fi
# Production acceptance must execute the real target-specific init ELF. The
# smoke ELF under kernel/tests is intentionally not an acceptable substitute.
# Fail before any QEMU attempts if one of the three release payloads is absent.
user_init_dir="$SOURCE/build/koronos/userspace"
missing_init=0
for required_target in live installer recovery; do
  required_init="$user_init_dir/${required_target}-init.elf"
  if [[ ! -s "$required_init" ]]; then
    echo "NOT RUN: missing production ${required_target} init ELF: $required_init" >&2
    missing_init=1
  fi
done
if [[ "$missing_init" -ne 0 ]]; then
  echo "ERROR: refusing to run a six-case matrix without all three production init ELFs; test probes do not satisfy this contract." >&2
  exit 2
fi

for target in live installer recovery; do
  tree="$matrix/${target}-tree"
  test_iso="$matrix/${target}.iso"
  rm -rf "$tree"
  mkdir -p "$tree/boot/grub"
  cp -a boot/iso/dist/iso/. "$tree/"
  test -s "$tree/boot/koronos/koronos.elf" || { echo "ERROR: ISO tree lacks Koronos ELF" >&2; exit 1; }
  mkdir -p "$tree/boot/user-init"
  cp -f "$user_init_dir/${target}-init.elf" "$tree/boot/user-init/${target}-init.elf"
  test -s "$tree/boot/user-init/${target}-init.elf" || { echo "ERROR: failed to stage ${target} production init ELF" >&2; exit 1; }
  cat > "$tree/boot/grub/grub.cfg" <<GRUB
set timeout=0
set default=0
terminal_output console
menuentry "Production acceptance ${target}" {
  multiboot2 /boot/koronos/koronos.elf chimera.target=${target} chm.log=verbose chm.progress=events
  module2 /boot/user-init/${target}-init.elf chimera-user-init-elf target=${target}
GRUB
  case "$target" in
    live)
      [[ ! -s "$tree/boot/live/chimera-live-initramfs.img" ]] || echo '  module2 /boot/live/chimera-live-initramfs.img chimera-live-initramfs' >> "$tree/boot/grub/grub.cfg"
      [[ ! -s "$tree/boot/live/live-manifest.json" ]] || echo '  module2 /boot/live/live-manifest.json chimera-live-manifest' >> "$tree/boot/grub/grub.cfg"
      ;;
    installer)
      for spec in \
        "install/installer/installation.img:chimera-installation-image" \
        "install/installer/installation-manifest.json:chimera-installation-manifest" \
        "install/installer/installer-contract.json:chimera-installer-contract" \
        "install/installer/installation_phases.json:chimera-install-phases" \
        "install/installer/installer_profiles.json:chimera-installer-profiles"; do
        rel="${spec%%:*}"
        label="${spec##*:}"
        [[ ! -s "$tree/$rel" ]] || echo "  module2 /$rel $label" >> "$tree/boot/grub/grub.cfg"
      done
      ;;
    recovery)
      [[ ! -s "$tree/boot/recovery/chimera-recovery-initramfs.img" ]] || echo '  module2 /boot/recovery/chimera-recovery-initramfs.img chimera-recovery-initramfs' >> "$tree/boot/grub/grub.cfg"
      [[ ! -s "$tree/boot/recovery/recovery-manifest.json" ]] || echo '  module2 /boot/recovery/recovery-manifest.json chimera-recovery-manifest' >> "$tree/boot/grub/grub.cfg"
      ;;
  esac
  cat >> "$tree/boot/grub/grub.cfg" <<'GRUB'
  boot
}
GRUB
  grub-mkrescue -o "$test_iso" "$tree" >/dev/null
  for firmware in bios uefi; do
    raw="$matrix/${target}-${firmware}.raw.log"
    trace="$matrix/${target}-${firmware}.log"
    rm -f "$raw" "$trace"
    qemu_args=(-machine q35 -m 1024 -smp 2 -accel tcg -cdrom "$test_iso" -boot d -display none -serial none -monitor none -no-reboot -no-shutdown -debugcon "file:$raw" -global isa-debugcon.iobase=0xe9)
    if [[ "$firmware" == "uefi" ]]; then
      vars_copy="$matrix/${target}-OVMF_VARS.fd"
      cp "$ovmf_vars" "$vars_copy"
      qemu_args+=(-drive "if=pflash,format=raw,unit=0,readonly=on,file=$ovmf_code" -drive "if=pflash,format=raw,unit=1,file=$vars_copy")
    fi
    set +e
    timeout 15s qemu-system-x86_64 "${qemu_args[@]}" > "$matrix/${target}-${firmware}-qemu.log" 2>&1
    qemu_rc=$?
    set -e
    printf 'QEMU BOOT PROVENANCE: target=%s firmware=%s\n' "$target" "$firmware" > "$trace"
    if [[ -s "$raw" ]]; then
      cat "$raw" >> "$trace"
    else
      printf '[HARNESS] QEMU emitted no debugcon bytes (exit=%s)\n' "$qemu_rc" >> "$trace"
    fi
    echo "Recorded independent $target/$firmware boot trace (QEMU exit $qemu_rc)."
  done
done
echo "Six fresh production-payload boot attempts captured. The unchanged verifier decides acceptance; this harness never synthesizes init markers."
