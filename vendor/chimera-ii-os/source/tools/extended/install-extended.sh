#!/usr/bin/env bash
# Chimera II OS - install the generated extended application payload into the rootfs.
# Usage: install-extended.sh ROOTFS APPS_OUT [REPOS_DIR]
set -euo pipefail

ROOTFS="${1:?rootfs path required}"
APPS_OUT="${2:?apps output path required}"
REPOS="${3:-}"

log(){ printf '[extended-install] %s\n' "$*"; }
[[ -d "$ROOTFS" ]] || { log "rootfs missing: $ROOTFS"; exit 1; }
[[ -d "$APPS_OUT" ]] || { log "apps output missing: $APPS_OUT"; exit 1; }

APPS_DST="$ROOTFS/opt/chimera/apps"
mkdir -p "$APPS_DST" \
         "$ROOTFS/usr/share/applications" \
         "$ROOTFS/usr/share/sounds" \
         "$ROOTFS/etc/systemd/system/multi-user.target.wants" \
         "$ROOTFS/etc/nginx/conf.d" \
         "$ROOTFS/etc/xdg" \
         "$ROOTFS/etc/skel/.config" \
         "$ROOTFS/opt/chimera/cockpit" \
         "$ROOTFS/opt/chimera/repos" \
         "$ROOTFS/usr/local/bin"

# 1. Application tree
cp -a "$APPS_OUT/." "$APPS_DST/"
chmod -R a+rX "$APPS_DST"
find "$APPS_DST/bin" -type f -exec chmod 0755 {} + 2>/dev/null || true
find "$APPS_DST/gui" -type f -name '*.py' -exec chmod 0755 {} + 2>/dev/null || true

# 2. Desktop entries
if [[ -d "$APPS_OUT/applications" ]]; then
  cp -f "$APPS_OUT/applications"/*.desktop "$ROOTFS/usr/share/applications/" 2>/dev/null || true
fi

# 3. Sounds (desktop event sound theme)
if [[ -d "$APPS_OUT/sounds" ]]; then
  cp -a "$APPS_OUT/sounds/." "$ROOTFS/usr/share/sounds/"
else
  mkdir -p "$ROOTFS/usr/share/sounds/chimera"
  for ev in startup shutdown login logout error notify click; do
    printf 'OggS' > "$ROOTFS/usr/share/sounds/chimera/$ev.oga" 2>/dev/null || true
  done
fi

# 4. Desktop / shell / terminal / input configuration
if [[ -d "$APPS_OUT/config" ]]; then
  for d in gtk-3.0 qt5ct sway labwc waybar shells terminals input xdg; do
    [[ -d "$APPS_OUT/config/$d" ]] || continue
    case "$d" in
      gtk-3.0)   mkdir -p "$ROOTFS/etc/skel/.config/gtk-3.0"; cp -a "$APPS_OUT/config/gtk-3.0/." "$ROOTFS/etc/skel/.config/gtk-3.0/" ;;
      qt5ct)     mkdir -p "$ROOTFS/etc/skel/.config/qt5ct"; cp -a "$APPS_OUT/config/qt5ct/." "$ROOTFS/etc/skel/.config/qt5ct/" ;;
      sway|labwc|waybar) mkdir -p "$ROOTFS/etc/chimera/$d"; cp -a "$APPS_OUT/config/$d/." "$ROOTFS/etc/chimera/$d/" ;;
      shells)    mkdir -p "$ROOTFS/etc/skel"
                 [[ -f "$APPS_OUT/config/shells/bash/.bashrc" ]] && cp -f "$APPS_OUT/config/shells/bash/.bashrc" "$ROOTFS/etc/skel/.bashrc"
                 [[ -f "$APPS_OUT/config/shells/zsh/.zshrc" ]] && cp -f "$APPS_OUT/config/shells/zsh/.zshrc" "$ROOTFS/etc/skel/.zshrc"
                 mkdir -p "$ROOTFS/etc/skel/.config/fish"
                 [[ -f "$APPS_OUT/config/shells/fish/.config/fish/config.fish" ]] && cp -f "$APPS_OUT/config/shells/fish/.config/fish/config.fish" "$ROOTFS/etc/skel/.config/fish/config.fish" ;;
      terminals) for t in foot alacritty kitty; do mkdir -p "$ROOTFS/etc/xdg/$t"; [[ -d "$APPS_OUT/config/terminals/$t" ]] && cp -a "$APPS_OUT/config/terminals/$t/." "$ROOTFS/etc/xdg/$t/"; done ;;
      input)     mkdir -p "$ROOTFS/etc/X11/xorg.conf.d" "$ROOTFS/etc/udev/rules.d"; cp -a "$APPS_OUT/config/input/." "$ROOTFS/etc/X11/xorg.conf.d/" 2>/dev/null || true ;;
      xdg)       mkdir -p "$ROOTFS/etc/xdg"; cp -a "$APPS_OUT/config/xdg/." "$ROOTFS/etc/xdg/" 2>/dev/null || true ;;
    esac
  done
fi

# 5. Helper tools
for t in chimera-control-center chimera-spotlight chimera-snap chimera-overview; do
  [[ -f "$APPS_OUT/bin/$t" ]] && install -Dm0755 "$APPS_OUT/bin/$t" "$ROOTFS/usr/local/bin/$t"
done

# 6. systemd units for exposed web apps
if [[ -d "$APPS_OUT/systemd" ]]; then
  cp -f "$APPS_OUT/systemd"/*.service "$ROOTFS/etc/systemd/system/" 2>/dev/null || true
  for u in "$APPS_OUT/systemd"/*.service; do
    [[ -f "$u" ]] || continue
    ln -sf "/etc/systemd/system/$(basename "$u")" \
      "$ROOTFS/etc/systemd/system/multi-user.target.wants/$(basename "$u")" 2>/dev/null || true
  done
fi

# 7. nginx reverse proxy + portal
if [[ -d "$APPS_OUT/nginx" ]]; then
  cp -f "$APPS_OUT/nginx"/*.conf "$ROOTFS/etc/nginx/conf.d/" 2>/dev/null || true
fi
python3 - "$APPS_OUT" "$ROOTFS" <<'PYEOF'
import json, os, sys
apps_out, rootfs = sys.argv[1], sys.argv[2]
web_path = os.path.join(apps_out, "web-apps.json")
web = json.load(open(web_path)) if os.path.exists(web_path) else []
www = os.path.join(rootfs, "var/www/chimera")
os.makedirs(www, exist_ok=True)
rows = "\n".join(
    '<li><a href="%s">%s</a> <span>%s</span></li>' % (w["path"], w["id"], w.get("repo",""))
    for w in web)
html = """<!doctype html><html><head><meta charset="utf-8">
<title>Chimera II OS - Applications</title>
<style>body{background:#0b0e14;color:#e8ecf4;font-family:system-ui;margin:0;padding:32px}
h1{color:#7fd1ff}ul{list-style:none;padding:0}li{padding:8px 0;border-bottom:1px solid #1d2430}
a{color:#9fe6a0;text-decoration:none}span{color:#6b7a90;font-size:12px;margin-left:8px}</style>
</head><body><h1>Chimera II OS Applications</h1>
<p class="sub">%d application web interfaces exposed from the project repositories.</p>
<ul>%s</ul></body></html>""" % (len(web), rows)
open(os.path.join(www, "index.html"), "w").write(html)
conf = """server {
    listen 80 default_server;
    server_name _;
    root /var/www/chimera;
    index index.html;

    location = /_chimera_auth {
        internal;
        proxy_pass http://127.0.0.1:9090/auth;
        proxy_pass_request_body off;
        proxy_set_header Content-Length "";
        proxy_set_header X-Original-URI $request_uri;
    }
    location / { try_files $uri $uri/ /index.html; }
}
"""
os.makedirs(os.path.join(rootfs, "etc/nginx/conf.d"), exist_ok=True)
open(os.path.join(rootfs, "etc/nginx/conf.d/chimera-portal.conf"), "w").write(conf)
print("portal entries:", len(web))
PYEOF

# 8. Cockpit-style administration console (RHEL cockpit clone)
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$HERE/cockpit/chimera_cockpit.py" ]]; then
  install -Dm0755 "$HERE/cockpit/chimera_cockpit.py" "$ROOTFS/opt/chimera/cockpit/chimera_cockpit.py"
  cat > "$ROOTFS/etc/systemd/system/chimera-cockpit.service" <<'EOF'
[Unit]
Description=Chimera II OS Cockpit-style administration console
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/chimera/cockpit/chimera_cockpit.py --port 9090
Restart=on-failure
Environment=CHIMERA_COCKPIT_PORT=9090

[Install]
WantedBy=multi-user.target
EOF
  ln -sf /etc/systemd/system/chimera-cockpit.service \
    "$ROOTFS/etc/systemd/system/multi-user.target.wants/chimera-cockpit.service" 2>/dev/null || true
  cat > "$ROOTFS/etc/nginx/conf.d/chimera-cockpit-proxy.conf" <<'EOF'
server {
    listen 9091;
    server_name _;
    location / { proxy_pass http://127.0.0.1:9090; proxy_set_header Host $host; }
}
EOF
  log "cockpit installed (9090, nginx 9091)"
fi

# 9. Repository sources
if [[ -n "$REPOS" && -d "$REPOS" ]]; then
  log "staging repository sources from $REPOS"
  for r in "$REPOS"/*/; do
    [[ -d "$r" ]] || continue
    n="$(basename "$r")"
    mkdir -p "$ROOTFS/opt/chimera/repos/$n"
    if command -v rsync >/dev/null 2>&1; then
      rsync -a --delete --exclude='.git/' --exclude='node_modules/' --exclude='__pycache__/' \
            "$r" "$ROOTFS/opt/chimera/repos/$n/" || true
    else
      cp -a "$r." "$ROOTFS/opt/chimera/repos/$n/" 2>/dev/null || true
    fi
  done
  log "repository sources staged: $(du -sh "$ROOTFS/opt/chimera/repos" 2>/dev/null | awk '{print $1}')"
fi

# 10. Graphical installer
if [[ -f "$HERE/installer/chimera-installer.py" ]]; then
  install -Dm0755 "$HERE/installer/chimera-installer.py" "$ROOTFS/usr/bin/chimera-installer"
  log "installed graphical installer: /usr/bin/chimera-installer"
fi
mkdir -p "$ROOTFS/etc/xdg/autostart"
cat > "$ROOTFS/usr/share/applications/chimera-installer.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Version=1.0
Name=Install Chimera II OS
Comment=Install Chimera II OS to a disk (erases the selected disk)
Exec=chimera-installer
Icon=drive-harddisk
Terminal=false
Categories=System;Settings;
Keywords=chimera;install;setup;deploy;
EOF
cat > "$ROOTFS/etc/xdg/autostart/chimera-installer.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Chimera II OS Installer
Comment=Start the installer when booted with chimera.installer=1
Exec=sh -c 'grep -qw chimera.installer=1 /proc/cmdline && exec chimera-installer'
Terminal=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
EOF

# 11. Emulator / retro desktop entries
REPO_ROOT="$(cd "$HERE/../.." && pwd)"
if [[ -d "$REPO_ROOT/emulators" ]]; then
  for e in "$REPO_ROOT"/emulators/*/; do
    [[ -d "$e" ]] || continue
    en="$(basename "$e")"
    mkdir -p "$ROOTFS/opt/chimera/emulators/$en"
    cat > "$ROOTFS/opt/chimera/emulators/$en/run.sh" <<EOF
#!/bin/sh
echo "Chimera II OS :: $en emulator"
if [ -x /usr/games/mame ]; then exec mame "\$@"; fi
if [ -x /usr/bin/mednafen ]; then exec mednafen "\$@"; fi
if [ -x /usr/bin/retroarch ]; then exec retroarch "\$@"; fi
echo "No emulator backend installed. Install mame, mednafen or retroarch."
exec bash
EOF
    chmod 0755 "$ROOTFS/opt/chimera/emulators/$en/run.sh"
    cat > "$ROOTFS/usr/share/applications/chimera-emulator-$en.desktop" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=Emulator: $en
Comment=Launch the $en emulator session from Chimera II OS
Exec=foot -e /opt/chimera/emulators/$en/run.sh
Icon=applications-games
Terminal=true
Categories=Game;Emulator;
Keywords=chimera;emulator;retro;$en;
EOF
    log "emulator desktop entry: $en"
  done
fi
cat > "$ROOTFS/usr/share/applications/chimera-playstation-hub.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Version=1.0
Name=PlayStation Emulator Hub
Comment=PSX / PS2 / PS3 / PS4 / PS5 emulator hub
Exec=sh -c 'if [ -x /usr/bin/firefox ]; then exec firefox /usr/share/chimera/web/playstation_emulators.html; else exec foot -e sh -c "echo PlayStation hub: /usr/share/chimera/web/playstation_emulators.html; exec bash"; fi'
Icon=applications-games
Terminal=false
Categories=Game;Emulator;
Keywords=chimera;playstation;psx;ps2;ps3;ps4;ps5;
EOF

# 12. Scripting-language shells / interpreters
mk_shell(){ # id name exec icon comment
  cat > "$ROOTFS/usr/share/applications/chimera-shell-$1.desktop" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=$2
Comment=$5
Exec=$3
Icon=$4
Terminal=true
Categories=System;TerminalEmulator;Development;
Keywords=chimera;shell;scripting;$1;
EOF
}
mk_shell sh "POSIX Shell (sh)" "foot -e sh -l" "utilities-terminal" "POSIX sh login shell"
mk_shell dash "Dash Shell" "foot -e dash -l" "utilities-terminal" "Debian Almquist shell"
mk_shell bash "Bash Shell" "foot -e bash -l" "utilities-terminal" "GNU Bourne-Again shell"
mk_shell zsh "Zsh Shell" "foot -e zsh -l" "utilities-terminal" "Z shell with Chimera config"
mk_shell fish "Fish Shell" "foot -e fish -l" "utilities-terminal" "Friendly interactive shell"
mk_shell ksh "Korn Shell (ksh)" "foot -e ksh -l" "utilities-terminal" "Korn shell"
mk_shell mksh "MirBSD Korn Shell (mksh)" "foot -e mksh -l" "utilities-terminal" "MirBSD Korn shell"
mk_shell tcsh "TCSH Shell" "foot -e tcsh -l" "utilities-terminal" "C shell variant"
mk_shell perl "Perl" "foot -e perl -de 1" "application-x-perl" "Perl debugger/REPL"
mk_shell ruby "Ruby (irb)" "foot -e irb" "application-x-ruby" "Ruby interactive shell"
mk_shell php "PHP (interactive)" "foot -e php -a" "application-x-php" "PHP interactive shell"
mk_shell lua "Lua" "foot -e lua" "text-x-lua" "Lua interactive shell"
mk_shell tcl "Tcl (tclsh)" "foot -e tclsh" "text-x-script" "Tcl shell"
mk_shell python "Python 3" "foot -e python3" "text-x-python" "Python 3 interactive shell"
mk_shell node "Node.js" "foot -e node" "applications-javascript" "Node.js REPL"
mk_shell awk "AWK (gawk)" "foot -e gawk -f /dev/stdin" "text-x-script" "GNU AWK"
mk_shell sed "Stream Editor (sed)" "foot -e bash -lc 'echo sed ready; exec bash'" "text-x-script" "GNU sed"
log "scripting-language desktop entries installed"

cat > "$ROOTFS/opt/chimera/apps/README.txt" <<'EOF'
Chimera II OS - Extended Application Payload
============================================
bin/          launchers for every Python GUI, Java, Node.js and static web app
gui/          generated Tkinter GUI wrappers for command-line Python programs
pyinstaller/  PyInstaller .spec files (build with: pyinstaller <spec>)
applications/ freedesktop .desktop entries (installed to /usr/share/applications)
systemd/      per-app units (enabled in multi-user.target)
nginx/        reverse-proxy snippets for /apps/<id>/ (system-user auth)
sounds/       Chimera sound theme
config/       desktop/shell/terminal/input configuration
web-apps.json catalogue of exposed web interfaces
app-catalog.json full catalogue of discovered applications
../repos/     complete source of every project repository
../cockpit/   Cockpit-style administration console (PAM, system users)
EOF

log "extended payload installed into $ROOTFS"
