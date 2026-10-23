# Process lifecycle root-cause review — 2026-10-23

OctavianOS must not mark target services ready based on module presence or a successful kernel handoff. The current vendored Koronos process API is admission/lookup/state bookkeeping, not a process supervisor. The target launch path loads one native init, enters ring 3 synchronously, then tears down its descriptors/address space when it exits. Native init intentionally prints `NATIVE INIT BLOCKED` and exits 78 after the VFS self-test because it cannot launch operational target services.

Required before readiness: parent/child process identity; spawn/exec; runnable child scheduling; wait/wakeup and exit status; generation-safe PID reuse; exactly-once reap and resource cleanup; pointer validation and race-safe transitions; a service supervisor with real health probes. A nested synchronous ring-3 entry is not a valid substitute for child process scheduling.

Installer storage persistence, production ring-3 filesystem traces, actual production ISO × six BIOS/UEFI target cases, Aurora/display health, Recovery repair postcondition, and AP-backed SMP remain independent gates. The closeout collector deliberately leaves them NOT RUN; DAPS must continue to reject the evidence report until actual raw production traces exist.

This is a source-level root-cause review, not an implementation or runtime PASS claim. Keep release blocked until code, tests, and production evidence agree.


## Remediation delta — 2026-10-23

The vendored source now contains a generation-tagged process handle API, parent PID+generation ownership, one-way exit/fault transitions, retained terminal children until parent wait/reap, and a guard against reaping a parent while it still owns descendants. The actual target launcher requests the generation-tagged handle and records exit/fault through the lifecycle API. The canonical Koronos build invokes `kernel/tests/process_lifecycle_test.cpp`, covering nested parent/child/grandchild relationships, status propagation, stale-handle invalidation, exactly-once terminal transitions, and registry reinitialization.

Verified on GitHub run [39955299994](https://github.com/amerhwitat/OctavianOS/actions/runs/39955299994): native Koronos build/source contracts and static routing both passed, including the DAPS missing-artifact CLI regression. The lifecycle API currently exposes a **nonblocking** wait result; it does not yet suspend/wake a scheduler-owned process context, launch concurrent ring-3 children, adopt orphaned descendants, or provide a complete resource-reaper. Thus it is lifecycle bookkeeping plus launcher terminal-state integration, not production process supervision.

The top-level DAPS CLI now supplies the evidence directory to validation, so missing artifacts, path traversal, SHA-256 mismatch, and missing/mismatched raw trace markers are checked from disk. The new top-level CLI regression passed in the static-routing workflow.

All independent production gates remain blocked until verified: installer storage-backed writable root and cold-reboot persistence; real ring-3 rootfs and writable `/tmp` traces; six production ISO target/firmware boots; Aurora/display health; Recovery repair postcondition; and AP-backed overlapping SMP. Do not infer these from the successful compile/source-contract run.
