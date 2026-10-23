# Linux-to-Koronos bootability gap analysis — OctavianOS vendor tree

Date: 2026-10-23

OctavianOS must preserve the Koronos runtime contract when vendoring kernel changes. Linux is an architectural reference, not a collection of files that can be copied into Koronos without its architecture glue, memory-management invariants, synchronization, configuration, and licensing review.

The source-level gap map and acceptance criteria are maintained in docs/LINUX_TO_KORONOS_BOOTABILITY_GAP_ANALYSIS.md in ChimeraIIOS. This OctavianOS copy records the required release policy:

- The native init currently fails closed with exit status 78 after diagnostic/VFS self-tests; it does not launch or supervise operational services.
- Live/Recovery archive staging and RAMFS/VFS mounting are not proof that ring-3 file operations have been observed in real production traces.
- Installer must not report readiness until a writable storage-backed target filesystem exists and a disposable-disk install survives cold reboot/readback.
- A service dependency/state graph is not a process supervisor. Spawn/exec, wait/reap, exit status, and resource cleanup must be implemented before operational target services can be supervised.
- Production acceptance requires the actual production ISO in Live/Installer/Recovery × BIOS/UEFI, plus independent Aurora health, recovery postcondition, and AP-backed concurrent SMP evidence.
- The closeout collector must use real ISO hashes and raw traces. Missing evidence means FAIL/NOT RUN; candidate probes and checker unit tests are not production acceptance.

Keep the PR draft and release publication blocked until the canonical build/tests and all runtime gates pass on the exact candidate commit. Do not synthesize readiness or relax the existing verifier to turn a failed boot green.
