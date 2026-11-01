#!/usr/bin/env bash
# Stage the OctavianOS userspace (desktops, apps, runtime) into the rootfs and
# wire a graphical kiosk session that runs the HTML desktop + all apps offline.
set -euo pipefail
REPO="${1:-/workspace/OctavianOS}"
ROOTFS="${2:-build/iso/rootfs}"
ROOTFS="$(cd "$(dirname "$ROOTFS")" && pwd)/$(basename "$ROOTFS")"
DEST="$ROOTFS/opt/octavianos"

rm -rf "$DEST"
mkdir -p "$DEST"/{apps,desktop,web,runtime}
cp -a "$REPO/apps/." "$DEST/apps/"
cp -a "$REPO/desktop/." "$DEST/desktop/"
cp -a "$REPO/web/." "$DEST/web/"
cp -a "$REPO/runtime/." "$DEST/runtime/"
cp -f "$REPO/README.md" "$DEST/README.md" 2>/dev/null || true

# Offline-correct the prototype desktop links: point remote GitHub Pages
# launchers at the locally staged applications so the ISO runs fully offline.
python3 - "$DEST" <<'PY'
import sys,pathlib
dest=pathlib.Path(sys.argv[1])
mapping={
 "https://amerhwitat.github.io/apps/aurora-glass-desktop/index.html":"/desktop/aurora-wayland-glass/index.html",
 "https://amerhwitat.github.io/apps/octavianos/marine/index.html":"/desktop/marine/index.html",
 "https://amerhwitat.github.io/apps/octavianos/aurora/index.html":"/desktop/aurora-wayland-glass/index.html",
 "https://amerhwitat.github.io/apps/index.html":"/apps/application-center.html",
 "https://amerhwitat.github.io/apps/chimera-ii-os/web/artifact-library.html":"/apps/application-center.html",
 "https://amerhwitat.github.io/apps/chimera-ii-os/web/aurora_terminal.html":"/apps/application-center.html",
 "https://amerhwitat.github.io/apps/chimera-ii-os/web/system_control_center.html":"/apps/application-center.html",
 "https://amerhwitat.github.io/apps/chimera-ii-os/web/health.html":"/apps/application-center.html",
 "https://amerhwitat.github.io/apps/repository-app-explorer/":"/apps/application-center.html",
}
for f in list(dest.rglob("*.html")):
    t=f.read_text(encoding="utf-8",errors="replace"); o=t
    for k,v in mapping.items(): t=t.replace(k,v)
    if t!=o: f.write_text(t,encoding="utf-8")
PY

# Home launcher: desktop choice + every bundled application.
cat > "$DEST/index.html" <<'HTML'
<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>OctavianOS</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}
body{margin:0;font-family:system-ui,Segoe UI,Roboto,sans-serif;color:#eaf2ff;
background:radial-gradient(1200px 600px at 20% 0%,#1b2a5e 0%,#0a0f1f 60%,#05070d 100%);
min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px}
h1{font-weight:800;letter-spacing:.06em;margin:0 0 6px}
p.sub{color:#9fb2d6;margin:0 0 28px}
h2{font-size:.8rem;letter-spacing:.18em;color:#7f93b8;text-transform:uppercase;margin:26px 0 12px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;max-width:980px;width:100%}
a.card{display:block;padding:18px;border-radius:16px;text-decoration:none;color:#eaf2ff;
background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);
backdrop-filter:blur(10px);transition:.18s}
a.card:hover{background:rgba(90,150,255,.18);border-color:#5a96ff;transform:translateY(-2px)}
a.card b{display:block;font-size:1.02rem;margin-bottom:4px}
a.card span{font-size:.82rem;color:#9fb2d6}
</style></head><body>
<h1>&#9672; OCTAVIANOS</h1><p class="sub">Chimera II OS &middot; Aurora &amp; Marine desktop runtime</p>
<h2>Desktop sessions</h2>
<div class="grid">
<a class="card" href="/desktop/aurora-wayland-glass/index.html"><b>Aurora Wayland Glass</b><span>macOS-inspired glass desktop</span></a>
<a class="card" href="/desktop/marine/index.html"><b>Marine Desktop</b><span>Windows-inspired shell</span></a>
</div>
<h2>Applications</h2>
<div class="grid">
<a class="card" href="/apps/application-center.html"><b>Application Center</b><span>Browse the full catalog</span></a>
<a class="card" href="/apps/paint-studio.html"><b>Paint Studio</b><span>Canvas drawing</span></a>
<a class="card" href="/apps/media-deck.html"><b>Media Deck</b><span>Audio/video player</span></a>
<a class="card" href="/apps/document-desk.html"><b>Document Desk</b><span>Notes &amp; documents</span></a>
<a class="card" href="/apps/snake-arcade.html"><b>Snake Arcade</b><span>Classic game</span></a>
<a class="card" href="/web/index.html"><b>Web Preview</b><span>Desktop preview page</span></a>
</div>
</body></html>
HTML

# Session launch helpers.
cat > "$DEST/launch-desktop.sh" <<'SH'
#!/bin/sh
# Launch a desktop session in the kiosk browser.
sess="${1:-aurora}"
case "$sess" in
  marine) url="http://127.0.0.1:8080/desktop/marine/index.html" ;;
  aurora|*) url="http://127.0.0.1:8080/desktop/aurora-wayland-glass/index.html" ;;
esac
exec chromium --kiosk --no-sandbox --disable-gpu --disable-dev-shm-usage \
  --user-data-dir=/tmp/chromium-kiosk --no-first-run --no-default-browser-check \
  "$url"
SH
cat > "$DEST/probe-desktop.sh" <<'SH'
#!/bin/sh
# Readiness probe: the local web server must answer and the desktop asset exist.
sess="${1:-aurora}"
case "$sess" in marine) p="/desktop/marine/index.html" ;; *) p="/desktop/aurora-wayland-glass/index.html" ;; esac
curl -fsS "http://127.0.0.1:8080$p" >/dev/null 2>&1 || exit 1
echo "DESKTOP READY: session=$sess"
SH
cat > "$DEST/kiosk.sh" <<'SH'
#!/bin/sh
xset -dpms s off 2>/dev/null || true
# Honour chm.desktop=aurora|marine from the kernel command line.
sess="aurora"
for a in $(cat /proc/cmdline 2>/dev/null); do
  case "$a" in chm.desktop=*) sess="${a#chm.desktop=}" ;; esac
done
exec /opt/octavianos/launch-desktop.sh "$sess"
SH
chmod +x "$DEST"/*.sh

# Session manifests.
mkdir -p "$ROOTFS/usr/share/octavianos/sessions"
cp -f "$REPO/desktop/sessions/aurora.json" "$ROOTFS/usr/share/octavianos/sessions/aurora.json"
cp -f "$REPO/desktop/sessions/marine.json" "$ROOTFS/usr/share/octavianos/sessions/marine.json"

# Local static web server for the desktop/app bundle.
cat > "$ROOTFS/etc/systemd/system/octavian-web.service" <<'UNIT'
[Unit]
Description=OctavianOS local app/desktop web server
After=network.target
[Service]
Type=simple
ExecStart=/usr/bin/python3 -m http.server 8080 --bind 127.0.0.1 --directory /opt/octavianos
Restart=always
[Install]
WantedBy=multi-user.target
UNIT

# Graphical kiosk session on tty1.
cat > "$ROOTFS/etc/systemd/system/octavian-kiosk.service" <<'UNIT'
[Unit]
Description=OctavianOS Aurora/Marine kiosk session
After=octavian-web.service systemd-user-sessions.service
Requires=octavian-web.service
[Service]
Type=simple
Environment=HOME=/root
ExecStart=/usr/bin/xinit /opt/octavianos/kiosk.sh -- :0 vt1 -keeptty -nolisten tcp
Restart=always
RestartSec=2
[Install]
WantedBy=graphical.target
UNIT

chroot "$ROOTFS" /bin/bash -c '
set -e
systemctl enable octavian-web.service octavian-kiosk.service >/dev/null 2>&1
systemctl set-default graphical.target >/dev/null 2>&1
mkdir -p /tmp /var/tmp
chmod 1777 /tmp /var/tmp
' || true

echo "[stage] userspace staged at $DEST"
