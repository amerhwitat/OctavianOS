# Process lifecycle root-cause review — 2026-10-23

OctavianOS must not mark target services ready based on module presence or a successful kernel handoff. The current vendored Koronos process API is admission/lookup/state bookkeeping, not a process supervisor. The target launch path loads one native init, enters ring 3 synchronously, then tears down its descriptors/address space when it exits. Native init intentionally prints `NATIVE INIT BLOCKED` and exits 78 after the VFS self-test because it cannot launch operational target services.

Required before readiness: parent/child process identity; spawn/exec; runnable child scheduling; wait/wakeup and exit status; generation-safe PID reuse; exactly-once reap and resource cleanup; pointer validation and race-safe transitions; a service supervisor with real health probes. A nested synchronous ring-3 entry is not a valid substitute for child process scheduling.

Installer storage persistence, production ring-3 filesystem traces, actual production ISO × six BIOS/UEFI target cases, Aurora/display health, Recovery repair postcondition, and AP-backed SMP remain independent gates. The closeout collector deliberately leaves them NOT RUN; DAPS must continue to reject the evidence report until actual raw production traces exist.

This is a source-level root-cause review, not an implementation or runtime PASS claim. Keep release blocked until code, tests, and production evidence agree.
