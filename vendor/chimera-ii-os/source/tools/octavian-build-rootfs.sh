#!/usr/bin/env bash
# OctavianOS userspace rootfs builder (Docker-free).
# Bootstraps a Debian rootfs and installs the graphical kiosk runtime that
# actually runs the repo's HTML desktops and applications offline.
set -euo pipefail
ROOTFS="${1:-build/iso/rootfs}"
ROOTFS="$(cd "$(dirname "$ROOTFS")" && pwd)/$(basename "$ROOTFS")"

cleanup_mounts() {
  for m in dev/pts dev proc sys run; do
    mountpoint -q "$ROOTFS/$m" 2>/dev/null && umount -lf "$ROOTFS/$m" 2>/dev/null || true
  done
}
trap cleanup_mounts EXIT

cp -f /etc/resolv.conf "$ROOTFS/etc/resolv.conf"
mkdir -p "$ROOTFS/proc" "$ROOTFS/sys" "$ROOTFS/dev" "$ROOTFS/run"
mount -t proc proc "$ROOTFS/proc"
mount -t sysfs sysfs "$ROOTFS/sys"
mount --bind /dev "$ROOTFS/dev"
mount -t devpts devpts "$ROOTFS/dev/pts" 2>/dev/null || true

export DEBIAN_FRONTEND=noninteractive
chroot "$ROOTFS" /bin/bash -c '
set -e
apt-get update -qq
apt-get install -y --no-install-recommends \
  systemd systemd-sysv udev dbus \
  linux-image-amd64 \
  live-boot live-boot-initramfs-tools initramfs-tools \
  xorg xinit openbox xserver-xorg-video-vesa xserver-xorg-video-fbdev \
  xserver-xorg-input-all x11-xserver-utils dbus-x11 \
  chromium fonts-dejavu-core fonts-liberation2 \
  python3 ca-certificates curl sudo \
  busybox-static pciutils usbutils \
  alsa-utils pulseaudio-utils \
  >/tmp/apt-install.log 2>&1 || { tail -40 /tmp/apt-install.log; exit 1; }
# A live image must have a real PID 1. systemd-sysv provides /sbin/init.
if [ ! -e /sbin/init ]; then
  ln -sfn /lib/systemd/systemd /sbin/init
fi
apt-get clean
rm -rf /var/lib/apt/lists/*

# Keep the live image small enough for the release media budget.
rm -rf /usr/share/doc/* /usr/share/man/* /usr/share/info/* \
       /usr/lib/python3*/test /usr/lib/python3*/idlelib \
       /usr/lib/gcc /var/cache/apt/* /var/lib/apt/lists/* 2>/dev/null || true
find /usr/lib/chromium/locales -mindepth 1 -maxdepth 1 ! -name "en-US*" -delete 2>/dev/null || true
'
echo "[rootfs] base packages installed"
