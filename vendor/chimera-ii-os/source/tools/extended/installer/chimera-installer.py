#!/usr/bin/env python3
"""
Chimera II OS - Aurora graphical installer

A dependency-free Tkinter installer launched from the Live CD (booted with
chimera.installer=1) or manually from a terminal.

It performs a real installation:
  1. enumerate block devices (lsblk)
  2. partition the chosen disk (GPT + ESP + root)
  3. format ESP (vfat) and root (ext4)
  4. unsquashfs the live filesystem onto the target
  5. generate /etc/fstab from UUIDs
  6. create the first user and set passwords
  7. install GRUB for x86_64-efi and i386-pc
  8. write the boot configuration

All destructive steps require an explicit confirmation checkbox.
"""
import os
import re
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox

APP = "Chimera II OS Installer"
VERSION = "1.0.0"
SQUASHFS_CANDIDATES = [
    "/run/live/medium/live/filesystem.squashfs",
    "/lib/live/mount/medium/live/filesystem.squashfs",
    "/cdrom/live/filesystem.squashfs",
    "/media/cdrom/live/filesystem.squashfs",
]


def run(cmd, check=True, timeout=None):
    """Run a command, returning (rc, stdout+stderr)."""
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, timeout=timeout)
    except FileNotFoundError:
        return 127, "missing executable: %s" % cmd[0]
    except subprocess.TimeoutExpired:
        return 124, "timeout: %s" % " ".join(cmd)
    out = p.stdout or ""
    if check and p.returncode != 0:
        raise RuntimeError("%s failed (%d):\n%s" % (" ".join(cmd), p.returncode, out))
    return p.returncode, out


def find_squashfs():
    for c in SQUASHFS_CANDIDATES:
        if os.path.isfile(c):
            return c
    for root in ("/run/live/medium", "/lib/live/mount/medium", "/cdrom", "/media"):
        if not os.path.isdir(root):
            continue
        for dirpath, _dirs, files in os.walk(root):
            if "filesystem.squashfs" in files:
                return os.path.join(dirpath, "filesystem.squashfs")
    return None


def _human(n):
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if n < 1024 or unit == "TiB":
            return ("%.1f %s" % (n, unit)) if unit != "B" else ("%d B" % n)
        n /= 1024.0


def list_disks():
    """Return [(name, size, model, is_removable)] for whole disks."""
    rc, out = run(["lsblk", "-d", "-b", "-n", "-o", "NAME,SIZE,MODEL,RM,TYPE"], check=False)
    disks = []
    if rc != 0:
        return disks
    for line in out.splitlines():
        parts = line.split(None, 4)
        if len(parts) < 5 or parts[4] != "disk":
            continue
        name, size, model, rm = parts[0], parts[1], parts[2], parts[3]
        try:
            human = _human(int(size))
        except ValueError:
            human = size
        disks.append(("/dev/" + name, human, model, rm == "1"))
    return disks


def part_path(disk, index):
    # /dev/sda -> /dev/sda1 ; /dev/nvme0n1 -> /dev/nvme0n1p1
    if re.search(r"\d$", disk):
        return "%sp%d" % (disk, index)
    return "%s%d" % (disk, index)


class Installer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("%s %s" % (APP, VERSION))
        self.geometry("860x620")
        self.minsize(760, 560)
        self.configure(bg="#1b1f24")
        self.squashfs = find_squashfs()
        self.disk_var = tk.StringVar()
        self.user_var = tk.StringVar(value="chimera")
        self.fullname_var = tk.StringVar(value="Chimera User")
        self.host_var = tk.StringVar(value="chimera")
        self.pass_var = tk.StringVar()
        self.pass2_var = tk.StringVar()
        self.confirm_var = tk.BooleanVar(value=False)
        self.efi_var = tk.BooleanVar(value=os.path.isdir("/sys/firmware/efi"))
        self._build_ui()
        self._load_disks()

    def _build_ui(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#1b1f24")
        style.configure("TLabel", background="#1b1f24", foreground="#e6edf3")
        style.configure("TLabelframe", background="#1b1f24", foreground="#e6edf3")
        style.configure("TLabelframe.Label", background="#1b1f24", foreground="#7ee787")
        style.configure("TButton", padding=6)
        style.configure("Header.TLabel", font=("DejaVu Sans", 18, "bold"), foreground="#58a6ff")

        head = ttk.Frame(self)
        head.pack(fill="x", padx=18, pady=(16, 6))
        ttk.Label(head, text="Install Chimera II OS", style="Header.TLabel").pack(anchor="w")
        ttk.Label(head, text="Aurora desktop  \u2022  Linux kernel  \u2022  Koronos verification").pack(anchor="w")

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=18, pady=8)

        diskf = ttk.LabelFrame(body, text="1. Target disk")
        diskf.pack(fill="x", pady=6)
        self.disk_combo = ttk.Combobox(diskf, textvariable=self.disk_var, state="readonly", width=60)
        self.disk_combo.pack(side="left", padx=8, pady=8)
        ttk.Button(diskf, text="Refresh", command=self._load_disks).pack(side="left", padx=4)
        self.disk_note = ttk.Label(diskf, text="", foreground="#f0883e")
        self.disk_note.pack(side="left", padx=8)

        sf = ttk.LabelFrame(body, text="2. Live filesystem")
        sf.pack(fill="x", pady=6)
        self.sq_label = ttk.Label(sf, text=self.squashfs or "NOT FOUND - mount the Live CD first",
                                  foreground="#7ee787" if self.squashfs else "#f85149")
        self.sq_label.pack(side="left", padx=8, pady=8)

        uf = ttk.LabelFrame(body, text="3. User account")
        uf.pack(fill="x", pady=6)
        grid = ttk.Frame(uf)
        grid.pack(fill="x", padx=8, pady=8)
        rows = [("Username", self.user_var, False),
                ("Full name", self.fullname_var, False),
                ("Hostname", self.host_var, False),
                ("Password", self.pass_var, True),
                ("Confirm", self.pass2_var, True)]
        for i, (label, var, secret) in enumerate(rows):
            ttk.Label(grid, text=label).grid(row=i, column=0, sticky="w", padx=4, pady=2)
            ttk.Entry(grid, textvariable=var, show="*" if secret else "").grid(
                row=i, column=1, sticky="we", padx=4, pady=2)
        grid.columnconfigure(1, weight=1)

        of = ttk.LabelFrame(body, text="4. Boot options")
        of.pack(fill="x", pady=6)
        ttk.Checkbutton(of, text="Install UEFI bootloader (x86_64-efi)", variable=self.efi_var).pack(
            side="left", padx=8, pady=8)
        ttk.Checkbutton(of, text="I understand the selected disk will be ERASED",
                        variable=self.confirm_var).pack(side="left", padx=8, pady=8)

        logf = ttk.LabelFrame(body, text="Progress")
        logf.pack(fill="both", expand=True, pady=6)
        self.log = tk.Text(logf, height=12, bg="#0d1117", fg="#c9d1d9", insertbackground="#c9d1d9",
                           relief="flat", wrap="word")
        self.log.pack(fill="both", expand=True, padx=6, pady=6)
        self.log.configure(state="disabled")

        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=18, pady=(0, 14))
        self.progress = ttk.Progressbar(bar, mode="determinate", maximum=100)
        self.progress.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.install_btn = ttk.Button(bar, text="Install", command=self._start)
        self.install_btn.pack(side="right")
        ttk.Button(bar, text="Quit", command=self.destroy).pack(side="right", padx=6)

    def _load_disks(self):
        disks = list_disks()
        values = ["%s  %s  %s%s" % (d[0], d[1], d[2], "  [removable]" if d[3] else "")
                  for d in disks]
        self.disk_combo["values"] = values
        if values and not self.disk_var.get():
            self.disk_var.set(values[0])
        if not values:
            self.disk_note.configure(text="no disks detected")

    def _log(self, msg):
        def append():
            self.log.configure(state="normal")
            self.log.insert("end", msg.rstrip() + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")
        self.after(0, append)

    def _set_progress(self, value):
        self.after(0, lambda: self.progress.configure(value=value))

    def _selected_disk(self):
        text = self.disk_var.get().strip()
        return text.split()[0] if text else ""

    def _validate(self):
        disk = self._selected_disk()
        if not disk:
            return "Select a target disk."
        if not self.squashfs:
            return "Live filesystem (filesystem.squashfs) was not found."
        if not self.confirm_var.get():
            return "Tick the confirmation box to allow erasing the disk."
        user = self.user_var.get().strip()
        if not re.match(r"^[a-z_][a-z0-9_-]{0,31}$", user):
            return "Username must be lowercase letters, digits, '_' or '-'."
        if self.pass_var.get() != self.pass2_var.get():
            return "Passwords do not match."
        if len(self.pass_var.get()) < 4:
            return "Password must be at least 4 characters."
        if os.geteuid() != 0:
            return "The installer must run as root."
        return None

    def _start(self):
        err = self._validate()
        if err:
            messagebox.showerror(APP, err)
            return
        self.install_btn.configure(state="disabled")
        threading.Thread(target=self._install_worker, daemon=True).start()

    def _install_worker(self):
        try:
            self._do_install()
            self._set_progress(100)
            self._log("\nInstallation complete. You may reboot into Chimera II OS.")
            self.after(0, lambda: messagebox.showinfo(APP, "Installation finished successfully."))
        except Exception as exc:  # noqa: BLE001 - surface any failure to the user
            self._log("\nERROR: %s" % exc)
            self.after(0, lambda: messagebox.showerror(APP, "Installation failed:\n%s" % exc))
        finally:
            self.after(0, lambda: self.install_btn.configure(state="normal"))

    def _do_install(self):
        disk = self._selected_disk()
        user = self.user_var.get().strip()
        fullname = self.fullname_var.get().strip() or user
        host = self.host_var.get().strip() or "chimera"
        password = self.pass_var.get()
        target = "/target"
        efi = self.efi_var.get()

        self._log("Target disk : %s" % disk)
        self._log("Live image  : %s" % self.squashfs)
        self._log("Firmware    : %s" % ("UEFI" if efi else "BIOS"))
        self._set_progress(3)

        run(["umount", "-R", target], check=False)
        os.makedirs(target, exist_ok=True)

        self._log("[1/8] Partitioning %s (GPT)" % disk)
        run(["parted", "-s", disk, "mklabel", "gpt"])
        if efi:
            run(["parted", "-s", disk, "mkpart", "ESP", "fat32", "1MiB", "513MiB"])
            run(["parted", "-s", disk, "set", "1", "esp", "on"])
            run(["parted", "-s", disk, "mkpart", "root", "ext4", "513MiB", "100%"])
            esp, root = part_path(disk, 1), part_path(disk, 2)
        else:
            run(["parted", "-s", disk, "mkpart", "bios_grub", "1MiB", "3MiB"])
            run(["parted", "-s", disk, "set", "1", "bios_grub", "on"])
            run(["parted", "-s", disk, "mkpart", "root", "ext4", "3MiB", "100%"])
            esp, root = None, part_path(disk, 1)
        run(["partprobe", disk], check=False)
        self._set_progress(12)

        self._log("[2/8] Formatting filesystems")
        if efi and esp:
            run(["mkfs.vfat", "-F32", "-n", "CHIMERA-ESP", esp])
        run(["mkfs.ext4", "-F", "-L", "chimera-root", root])
        self._set_progress(20)

        self._log("[3/8] Mounting target")
        run(["mount", root, target])
        if efi and esp:
            os.makedirs(os.path.join(target, "boot/efi"), exist_ok=True)
            run(["mount", esp, os.path.join(target, "boot/efi")])
        self._set_progress(25)

        self._log("[4/8] Unpacking live filesystem (this takes a while)")
        run(["unsquashfs", "-f", "-d", target, self.squashfs])
        self._set_progress(62)

        self._log("[5/8] Writing /etc/fstab")
        root_uuid = self._uuid(root)
        lines = ["# /etc/fstab - generated by chimera-installer",
                 "UUID=%s  /  ext4  errors=remount-ro  0  1" % root_uuid]
        if efi and esp:
            lines.append("UUID=%s  /boot/efi  vfat  umask=0077  0  1" % self._uuid(esp))
        lines.append("tmpfs  /tmp  tmpfs  defaults,nosuid,nodev  0  0")
        self._write(os.path.join(target, "etc/fstab"), "\n".join(lines) + "\n")
        self._set_progress(66)

        self._log("[6/8] Creating user %s and setting hostname" % user)
        self._write(os.path.join(target, "etc/hostname"), host + "\n")
        self._bind_mounts(target)
        run(["chroot", target, "useradd", "-m", "-s", "/bin/bash", "-c", fullname, "-G",
             "sudo,audio,video,plugdev,netdev", user], check=False)
        run(["chroot", target, "usermod", "-aG", "sudo", user], check=False)
        p1 = subprocess.run(["chroot", target, "chpasswd"], input="%s:%s\n" % (user, password),
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if p1.returncode != 0:
            self._log("  warning: chpasswd failed: %s" % (p1.stdout or "").strip())
        run(["chroot", target, "passwd", "-d", "root"], check=False)
        self._set_progress(72)

        self._log("[7/8] Installing GRUB")
        if efi:
            run(["chroot", target, "grub-install", "--target=x86_64-efi",
                 "--efi-directory=/boot/efi", "--bootloader-id=chimera",
                 "--removable", "--no-nvram"], check=False)
        run(["chroot", target, "grub-install", "--target=i386-pc", disk], check=False)
        run(["chroot", target, "update-grub"], check=False)
        self._set_progress(90)

        self._log("[8/8] Finishing up")
        run(["umount", "-R", target], check=False)
        self._set_progress(96)

    @staticmethod
    def _uuid(dev):
        rc, out = run(["blkid", "-s", "UUID", "-o", "value", dev], check=False)
        return out.strip() if rc == 0 and out.strip() else ""

    @staticmethod
    def _write(path, text):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def _bind_mounts(self, target):
        for fs in ("proc", "sys", "dev", "dev/pts", "run"):
            src = "/" + fs
            dst = os.path.join(target, fs)
            os.makedirs(dst, exist_ok=True)
            run(["mount", "--bind", src, dst], check=False)


def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return 0
    if "--version" in sys.argv:
        print(VERSION)
        return 0
    app = Installer()
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
