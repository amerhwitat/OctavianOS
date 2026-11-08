#!/usr/bin/env bash
# Stage real open-source shells and terminal emulators into an ISO rootfs.
# APT verifies repository metadata/signatures; dependency packages are extracted
# into the target rootfs without installing them on the build host.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEST="${CHIMERA_ROOTFS_DIR:?CHIMERA_ROOTFS_DIR must point at the target rootfs}"
WORK="${CHIMERA_TERMINAL_PACKAGE_WORK:-${CHIMERA_BUILD_DIR:-$ROOT/build}/terminal-packages}"
REQUIRE_ALL="${CHIMERA_TERMINAL_REQUIRE_ALL:-0}"
mkdir -p "$WORK/archives" "$WORK/extracted" "$DEST/usr/bin" "$DEST/usr/share/chimera/aurora"
for tool in apt-get apt-cache dpkg-deb python3 readelf; do
  command -v "$tool" >/dev/null 2>&1 || { echo "[AURORA-TERMINALS] required staging tool missing: $tool" >&2; exit 1; }
done
declare -A PACKAGE_BIN=(
  [bash]=bash [zsh]=zsh [fish]=fish [dash]=dash [mksh]=mksh
  [yash]=yash [elvish]=elvish [nushell]=nu
  [xterm]=xterm [gnome-terminal]=gnome-terminal [gnome-console]=kgx [konsole]=konsole
  [xfce4-terminal]=xfce4-terminal [foot]=foot [kitty]=kitty [ptyxis]=ptyxis
  [alacritty]=alacritty [wezterm]=wezterm [ghostty]=ghostty [contour]=contour
  [terminator]=terminator [tilix]=tilix [mate-terminal]=mate-terminal [qterminal]=qterminal
  [sakura]=sakura [terminology]=terminology [lxterminal]=lxterminal [blackbox-terminal]=blackbox
)
declare -A APT_PACKAGE=(
  [bash]=bash [zsh]=zsh [fish]=fish [dash]=dash [mksh]=mksh
  [yash]=yash [elvish]=elvish [nushell]=nushell
  [xterm]=xterm [gnome-terminal]=gnome-terminal [gnome-console]=gnome-console [konsole]=konsole
  [xfce4-terminal]=xfce4-terminal [foot]=foot [kitty]=kitty [ptyxis]=ptyxis
  [alacritty]=alacritty [wezterm]=wezterm [ghostty]=ghostty [contour]=contour
  [terminator]=terminator [tilix]=tilix [mate-terminal]=mate-terminal [qterminal]=qterminal
  [sakura]=sakura [terminology]=terminology [lxterminal]=lxterminal [blackbox-terminal]=blackbox-terminal
  [flatpak]=flatpak
)
declare -A SOURCE_BUILD_BIN=(
  [bash]=bash [zsh]=zsh [fish]=fish [dash]=dash [mksh]=mksh
  [yash]=yash [elvish]=elvish [nushell]=nu
  [alacritty]=alacritty [foot]=foot [blackbox-terminal]=blackbox
  [wezterm]=wezterm [ghostty]=ghostty [contour]=contour
)
SOURCE_REQUIRED="$DEST/usr/share/chimera/aurora/terminal-shell-source-required.tsv"
: > "$SOURCE_REQUIRED"
echo "[AURORA-TERMINALS] Updating signed APT metadata"
if [[ "$(id -u)" -eq 0 ]]; then APT=(apt-get); else command -v sudo >/dev/null 2>&1 || { echo "[AURORA-TERMINALS] sudo required for signed package metadata/downloads" >&2; exit 1; }; APT=(sudo apt-get); fi
"${APT[@]}" update -o Acquire::Retries=5
AVAILABLE=()
for id in "${!APT_PACKAGE[@]}"; do
  pkg="${APT_PACKAGE[$id]}"
  candidate="$(apt-cache policy "$pkg" 2>/dev/null | awk '/Candidate:/ {print $2; exit}' || true)"
  if [[ -n "$candidate" && "$candidate" != "(none)" ]]; then
    AVAILABLE+=("$pkg")
  else
    echo "[AURORA-TERMINALS] no signed distro package candidate for $id ($pkg); source build required"
    binary="${SOURCE_BUILD_BIN[$id]:-}"
    if [[ -n "$binary" && ! -x "$DEST/usr/local/bin/$binary" && ! -x "$DEST/usr/bin/$binary" ]]; then
      printf '%s|%s|distribution-provider-unavailable-source-build-required\n' "$id" "$binary" >> "$SOURCE_REQUIRED"
    fi
  fi
done
if (("${#AVAILABLE[@]}")); then
  chmod 0755 "$WORK/archives"
  "${APT[@]}" install --download-only --reinstall --no-install-recommends -y \
    -o "Dir::Cache::archives=$WORK/archives" "${AVAILABLE[@]}"
  # APT may leave successfully fetched archives in nested cache directories
  # (notably archives/partial when downloads run through sudo). Walk the cache
  # recursively rather than assuming a single directory depth. The download is
  # authenticated by APT repository metadata; make completed files readable
  # to this extraction process before invoking dpkg-deb.
  # sudo apt-get may create archives/partial as root/_apt with mode 0700.
  # Make every cache directory searchable and every authenticated .deb readable
  # before the unprivileged extraction process walks the tree.
  if [[ "$EUID" -eq 0 ]]; then
    chmod -R a+rX "$WORK/archives"
  elif command -v sudo >/dev/null 2>&1; then
    sudo chmod -R a+rX "$WORK/archives"
  else
    echo "[AURORA-TERMINALS] cannot read nested APT archives without sudo chmod" >&2
    exit 2
  fi
  mapfile -d '' package_archives < <(find "$WORK/archives" -type f -name '*.deb' -print0)
  (("${#package_archives[@]}")) || { echo "[AURORA-TERMINALS] APT reported success but produced no package archives under $WORK/archives" >&2; exit 2; }
  printf '[AURORA-TERMINALS] extracting %s authenticated package archives\n' "${#package_archives[@]}"
  for deb in "${package_archives[@]}"; do
    if [[ "$EUID" -eq 0 ]]; then
      chmod a+r "$deb"
    elif command -v sudo >/dev/null 2>&1; then
      sudo chmod a+r "$deb"
    else
      echo "[AURORA-TERMINALS] cannot read root-owned APT archive without sudo: $deb" >&2
      exit 2
    fi
    dpkg-deb -x "$deb" "$WORK/extracted"
  done
  # Overlay complete authenticated package payload. Do not use cp -n: stale
  # paths or dangling links must not suppress genuine package executables.
  cp -a "$WORK/extracted/." "$DEST/"
  for binary in xterm gnome-terminal kgx konsole xfce4-terminal foot kitty ptyxis alacritty wezterm ghostty contour terminator tilix mate-terminal qterminal sakura terminology lxterminal blackbox; do
    if [[ -x "$WORK/extracted/usr/bin/$binary" || -x "$WORK/extracted/usr/local/bin/$binary" ]]; then
      printf '[AURORA-TERMINALS] extracted provider: %s\n' "$binary"
    fi
  done
fi
if [[ -s "$SOURCE_REQUIRED" ]]; then
  repo_dir="$(git -C "$ROOT" rev-parse --show-toplevel 2>/dev/null || true)"
  source_builder="${CHIMERA_TERMINAL_SOURCE_BUILDER:-$repo_dir/live-image/lib/build-terminal-shell-sources.sh}"
  [[ -f "$source_builder" ]] || { echo "[AURORA-TERMINALS] missing source-build provider driver: $source_builder" >&2; exit 2; }
  echo "[AURORA-TERMINALS] building source-required providers from pinned upstream revisions"
  bash "$source_builder" "$DEST" "$WORK/source-build"
fi
repo_dir="$(git -C "$ROOT" rev-parse --show-toplevel 2>/dev/null || true)"
ptyxis_helper="${CHIMERA_PTYXIS_FLATPAK_HELPER:-$repo_dir/live-image/lib/install-ptyxis-flatpak.sh}"
[[ -f "$ptyxis_helper" ]] || { echo "[AURORA-TERMINALS] missing signed Ptyxis Flatpak integration helper: $ptyxis_helper" >&2; exit 2; }
bash "$ptyxis_helper" "$DEST" "$WORK/ptyxis-flatpak"
python3 - "$DEST" "$REQUIRE_ALL" "${CHIMERA_TARGET_ARCH:-$(uname -m)}" <<'PY'
import hashlib,json,pathlib,shutil,subprocess,sys,platform
dest=pathlib.Path(sys.argv[1]); require_all=sys.argv[2]=="1"; target=sys.argv[3]; readelf=shutil.which("readelf")
machines={"x86_64":"Advanced Micro Devices X86-64","amd64":"Advanced Micro Devices X86-64","aarch64":"AArch64","arm64":"AArch64","i686":"Intel 80386","i386":"Intel 80386","riscv64":"RISC-V","ppc64le":"PowerPC64","s390x":"IBM S/390"}
expected=machines.get(target,target)
rows=[
 ("bash","shell","bash"),("zsh","shell","zsh"),("fish","shell","fish"),("dash","shell","dash"),
 ("mksh","shell","mksh"),("yash","shell","yash"),("elvish","shell","elvish"),("nushell","shell","nu"),
 ("xterm","terminal","xterm"),("gnome-terminal","terminal","gnome-terminal"),("gnome-console","terminal","kgx"),("konsole","terminal","konsole"),
 ("xfce4-terminal","terminal","xfce4-terminal"),("foot","terminal","foot"),("kitty","terminal","kitty"),("ptyxis","terminal","ptyxis"),
 ("alacritty","terminal","alacritty"),("wezterm","terminal","wezterm"),("ghostty","terminal","ghostty"),("contour","terminal","contour"),
 ("terminator","terminal","terminator"),("tilix","terminal","tilix"),("mate-terminal","terminal","mate-terminal"),("qterminal","terminal","qterminal"),
 ("sakura","terminal","sakura"),("terminology","terminal","terminology"),("lxterminal","terminal","lxterminal"),("blackbox-terminal","terminal","blackbox")]
manifest=[]
for ident,kind,binary in rows:
    candidates=[dest/"usr/local/bin"/binary,dest/"usr/bin"/binary,dest/"bin"/binary]
    path=next((p for p in candidates if p.is_file() and p.stat().st_mode&0o111),None)
    row={"id":ident,"kind":kind,"binary":binary,"status":"unavailable","runtime_status":"not-runtime-tested"}
    if path:
        row.update(status="binary-present",path="/"+str(path.relative_to(dest)),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        data=path.read_bytes()
        if data.startswith(b"#!"):
            first=data.splitlines()[0][2:].decode("utf-8","replace").strip().split()
            interpreter=first[0] if first else ""
            if interpreter.endswith("/env") and len(first)>1:
                candidate=first[1]
                interp=next((dest/d/candidate for d in ("usr/bin","bin","usr/local/bin") if (dest/d/candidate).is_file()),None)
                env_path=dest/interpreter.lstrip("/")
                valid=env_path.is_file() and interp is not None
            else:
                interp=dest/interpreter.lstrip("/") if interpreter.startswith("/") else None
                valid=interp is not None and interp.is_file() and bool(interp.stat().st_mode&0o111)
            if valid and kind=="shell":
                rel="/"+str(path.relative_to(dest))
                try:
                    probe=subprocess.run(["chroot",str(dest),rel,"-c","printf CHIMERA_SHELL_SMOKE"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=12)
                    ok=probe.returncode==0 and b"CHIMERA_SHELL_SMOKE" in probe.stdout
                    row["status"]="verified-script-provider" if ok else "script-smoke-failed"
                    row["runtime_status"]="shell-command-smoke-pass" if ok else "script-smoke-failed"
                except (OSError,subprocess.TimeoutExpired):
                    row["status"]="script-smoke-failed"; row["runtime_status"]="script-smoke-failed"
            elif valid:
                # A terminal emulator needs a real display/input session. A
                # --version call without Xorg/Wayland is not a GUI acceptance
                # test and must not misclassify a genuine staged executable.
                row["status"]="verified-script-provider"
                row["runtime_status"]="not-gui-tested"
            else:
                row["status"]="script-interpreter-missing"
        elif readelf:
            proc=subprocess.run([readelf,"-h",str(path)],text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
            machine=next((x.split(":",1)[1].strip() for x in proc.stdout.splitlines() if x.strip().startswith("Machine:")),None)
            if proc.returncode or not machine: row["status"]="present-but-not-valid-ELF"
            elif expected not in machine and machine not in expected: row["status"]="wrong-architecture"
            else:
                row["elf_machine"]=machine
                host=platform.machine()
                aliases={"amd64":"x86_64","arm64":"aarch64"}
                if kind=="shell" and aliases.get(host,host)==aliases.get(target,target):
                    try:
                        probe=subprocess.run([str(path),"-c","printf CHIMERA_SHELL_SMOKE"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=12)
                        ok=probe.returncode==0 and b"CHIMERA_SHELL_SMOKE" in probe.stdout
                        row["runtime_status"]="shell-command-smoke-pass" if ok else "shell-command-smoke-fail"
                        if not ok:
                            row["status"]="shell-command-smoke-fail"
                    except (OSError,subprocess.TimeoutExpired):
                        row["status"]="shell-command-smoke-fail"; row["runtime_status"]="shell-command-smoke-fail"
                elif kind=="terminal":
                    row["runtime_status"]="not-gui-tested"
                else:
                    row["runtime_status"]="not-runnable-on-builder"
        else: row["status"]="present-hash-only"
    if row["id"] == "ptyxis":
        flatpak_meta = dest / "usr/share/chimera/aurora/ptyxis-flatpak-provider.json"
        try:
            meta = json.loads(flatpak_meta.read_text(encoding="utf-8"))
            valid_flatpak = (meta.get("app_id") == "app.devsuite.Ptyxis"
                             and meta.get("remote") == "flathub"
                             and meta.get("branch") == "stable"
                             and meta.get("signature_verified") is True
                             and bool(meta.get("commit")) and bool(meta.get("runtime"))
                             and bool(meta.get("app_binary_sha256")))
        except (OSError, json.JSONDecodeError):
            valid_flatpak = False
            meta = {}
        if valid_flatpak:
            row["provider_type"] = "flatpak"
            row["flatpak_app_id"] = meta["app_id"]
            row["flatpak_commit"] = meta["commit"]
            row["flatpak_runtime"] = meta["runtime"]
            row["flatpak_signature_verified"] = True
            row["flatpak_app_binary_sha256"] = meta["app_binary_sha256"]
        else:
            row["status"] = "flatpak-verification-failed"
    manifest.append(row)
out={"schema":"AURORA-TERMINAL-SHELL-STAGING-1","policy":"Only real executable files are listed; SHA-256 identifies exact bytes; staging does not imply runtime compatibility.","entries":manifest}
p=dest/"usr/share/chimera/aurora/terminal-shell-staging.json"; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,indent=2)+"\n")
missing=[r["id"] for r in manifest if r["status"] not in ("binary-present","verified-script-provider") or (r["kind"]=="shell" and r["runtime_status"]!="shell-command-smoke-pass")]
print(f"[AURORA-TERMINALS] staged={len(manifest)-len(missing)}/{len(manifest)} missing={','.join(missing) if missing else 'none'}")
if require_all and missing: raise SystemExit("required terminal/shell binaries missing: "+", ".join(missing))
PY
