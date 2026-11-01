#!/usr/bin/env bash
# OctavianOS live rootfs orchestrator (Docker-free).
#
# 1. debootstrap a Debian bookworm minbase with systemd as PID 1
# 2. install the graphical kiosk runtime (Xorg + Chromium + live-boot)
# 3. stage the repository's desktops and applications under /opt/octavianos
#
# Usage: sudo tools/octavian-build-live-rootfs.sh [rootfs-dir]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOTFS="${1:-$SOURCE_DIR/build/iso/rootfs}"
SUITE="${CHIMERA_DEBIAN_SUITE:-bookworm}"
MIRROR="${CHIMERA_DEBIAN_MIRROR:-http://deb.debian.org/debian}"

log(){ printf '[live-rootfs] %s\n' "$*"; }

if [[ $EUID -ne 0 ]]; then
  echo "[live-rootfs] must run as root" >&2
  exit 1
fi

if [[ ! -d "$ROOTFS/etc" ]]; then
  log "Debootstrapping Debian $SUITE into $ROOTFS"
  mkdir -p "$ROOTFS"
  debootstrap --arch=amd64 --variant=minbase \
    --include=systemd-sysv,ca-certificates,apt-utils,curl \
    "$SUITE" "$ROOTFS" "$MIRROR"
else
  log "Reusing existing rootfs at $ROOTFS"
fi

log "Installing graphical kiosk runtime"
bash "$SCRIPT_DIR/octavian-build-rootfs.sh" "$ROOTFS"

log "Staging OctavianOS desktops and applications"
REPO_ROOT="$(cd "$SOURCE_DIR/../../.." && pwd)"
bash "$SCRIPT_DIR/octavian-stage-userspace.sh" "$REPO_ROOT" "$ROOTFS"

log "Live rootfs ready: $ROOTFS"
