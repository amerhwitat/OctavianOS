# OctavianOS native Koronos acceptance boundary

The vendored Koronos source carries the same six-case verifier as ChimeraIIOS:

- `vendor/chimera-ii-os/source/tools/boot/verify-six-case-matrix.py`
- `vendor/chimera-ii-os/source/tests/boot/test_six_case_matrix.py`
- `vendor/chimera-ii-os/source/docs/KORONOS_SIX_CASE_ACCEPTANCE.md`

The Koronos userspace workflow currently builds per-target probe ISOs with test
init ELFs. These are candidate ring-3 launch tests only. They do not prove that
one immutable native Koronos ISO boots Live, Installer and Recovery under BIOS
and UEFI, nor do they prove production VFS, Aurora/Marine, installer persistence,
recovery repair or real SMP.

OctavianOS's separate live-image builder uses a Debian Linux kernel and systemd
userspace. Its successful Linux live boot is useful desktop evidence, but is not
native Koronos acceptance and must not be substituted for it.

Native Koronos release status remains BLOCKED until the six-case verifier
accepts evidence bound to the canonical ISO SHA-256. Native-init exit 78,
CPL3-originated syscall acknowledgement, matching nonzero PID, VFS, SMP,
desktop readiness, installer persistence and recovery postcondition remain
fail-closed requirements.

## Same-ISO QEMU evidence collection

The diagnostic runner is `vendor/chimera-ii-os/source/tools/boot/run-six-case-qemu.py`. It boots the canonical ISO for each target and firmware case without remastering the ISO between runs, hashes the ISO before and after each boot, and preserves raw debugcon/serial traces. UEFI uses matched OVMF code and per-case writable variable stores. GRUB passes its actual `grub_platform` value to the target-init module; Koronos emits the BIOS/UEFI identity marker.

The runner does not synthesize any acceptance evidence. It cannot make a case PASS by itself: the six-case verifier still requires real CPL3 PID handoff, root VFS and writable `/tmp`, two-CPU overlap, Aurora/Marine session traces, installer cold-boot persistence and Recovery repair postcondition. Current console/dry-run/diagnostic target payloads remain insufficient for production acceptance.
