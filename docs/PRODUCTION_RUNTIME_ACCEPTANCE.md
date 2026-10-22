# Production Runtime Acceptance Gate

This document defines the release-blocking evidence required for a production ISO. It is not a statement that the requirements currently pass.

## Required execution evidence

A kernel heartbeat, module registry entry, parsed manifest, load-plan-only ELF admission, candidate probe, or presence of desktop assets is not userspace readiness.

For each production boot, the serial/debug trace must contain these ordered events for the same nonzero PID:

1. `KERNEL_READY`
2. `USER_SYSCALL pid=<N> syscall=<supported-init-ack>` — emitted only after the syscall originates from the running CPL3 init process; kernel-side synthetic markers are forbidden.
3. `USERSPACE_READY target=<live|installer|recovery> pid=<N>` — emitted only after the acknowledgement is validated and the init process is alive.

The verifier must reject missing, duplicated/out-of-order, zero or mismatched PID events, wrong-target events, and markers produced by a candidate/probe executable. Every failure must include the phase, target, firmware mode, and reason. A timeout is a failure, never a pass.

## Mandatory production matrix

Run each case against the exact release-candidate ISO and record artifact SHA-256, commit SHA, firmware configuration, raw serial log, verifier output, and PASS/FAIL/NOT RUN:

| Target | BIOS | UEFI |
|---|---|---|
| Live | Required | Required |
| Installer | Required | Required |
| Recovery | Required | Required |

Do not infer one firmware result from the other. Do not mark unexecuted cases PASS.

## End-to-end checks after userspace starts

- Live: real initramfs init process, user-originated syscall, Aurora/session manager startup, compositor/session handoff, and usable desktop; desktop files alone are insufficient.
- Installer: installer process starts from installer media, discovers supported storage, performs a test installation to a disposable disk, reboots, and boots the installed target.
- Recovery: repair shell starts from recovery media and executes a harmless diagnostic command.
- Storage: write known data, flush, cold power-cycle/restart the VM, reattach the same disk, and verify the data; in-memory or RAM-disk-only tests do not qualify.
- SMP: start application processors using the platform startup protocol, confirm per-CPU identity and scheduler participation, and demonstrate overlapping work on at least two distinct CPUs. A reported CPU count is not proof.
- Mirror parity: repeat the same checks against the OctavianOS source and its own production-built ISO. Upstream results cannot stand in for OctavianOS evidence.

## Implementation dependencies (must be real, not mocked)

1. ELF loader: validate headers and arithmetic; map PT_LOAD pages; copy file bytes; zero BSS; enforce segment permissions and NX/W^X; handle mapping failures safely.
2. Process address spaces: preserve required kernel mappings while providing isolated user mappings, a valid user stack, and cleanup on exit/fault.
3. x86-64 privilege transition: correct GDT/TSS/RSP0 setup, ring-3 entry, syscall/interrupt entry and safe return, plus user-fault diagnostics.
4. Target selection: exactly one explicit Live/Installer/Recovery target; require its matching init executable and dependencies; fail closed if absent or inconsistent.
5. Runtime services: register real block-device backends, mount persistent storage, and only report services RUNNING after start callbacks and independent health checks succeed.
6. SMP: AP trampoline/startup, per-CPU state and stacks, synchronization, scheduler dispatch and concurrency tests.

## Release rule

The gate passes only if all six firmware/target combinations and all applicable end-to-end checks pass on the exact artifacts intended for publication. Keep release publication blocked on any FAIL or NOT RUN. Store logs and artifact hashes with the CI run. Never synthesize success markers or weaken this gate to obtain a green dashboard.

## Current branch evidence status (2026-10-22)

This section records observed gaps on the OctavianOS working branch; it does not waive any gate above.

- The target-specific native init binaries in `kernel/userspace/native_init.c` currently perform a CPL3 syscall acknowledgement, validate that the selected data payload exists, emit `USERSPACE READY: <target> init pid=<N>`, and exit. Their own source explicitly limits that marker to the native-init ABI milestone. It does not mount the initramfs, start Aurora, run installer actions, or provide a recovery shell.
- `core/koronos.cpp` currently logs explicit withheld states for Live, Installer, and Recovery when no supported target runtime is wired. These messages are release blockers and must not be treated as successful handoff.
- `core/scheduler.cpp` deliberately returns zero from `chimera_sched_run_parallel()`; its comments state that no AP workers enter the scheduler from independent CPUs. SMP is NOT RUN / FAIL until AP startup, per-CPU state, scheduler participation, and overlapping work on distinct CPUs are demonstrated.
- The acceptance workflow must fail closed if any withheld-handoff message is present or if the target-specific runtime readiness marker is absent. A green legacy ring-3 smoke run is evidence for the ABI probe only, not production target acceptance.
- Native Koronos build workflow run `39764511700` had no jobs exposed at the last status inspection; its result is unresolved, not PASS.
- The refreshed six-case acceptance workflow run `39764511575` was still executing at the last inspection. It is not a completed release result.

### Implementation work still required

1. Implement a native userspace init/runtime that consumes the selected target payload through a real, supported archive/VFS interface and reports service readiness only after the services actually start.
2. Live: mount and start the production initramfs, supervise the session, start the Aurora compositor/session manager, and prove the session is usable.
3. Installer: implement and execute a target-owned installer runtime, perform a disposable-disk installation, reboot, and verify the installed system boots.
4. Recovery: implement a target-owned recovery runtime and prove a repair shell can execute a harmless diagnostic command.
5. Storage: implement/verify a real persistent block backend and filesystem mount; write, flush, cold-reboot, reattach, and verify data.
6. SMP: implement AP startup/trampoline, per-CPU stacks/state and scheduler workers, then demonstrate overlapping work on at least two CPUs.
7. Capture commit and ISO hashes, raw logs, verifier output, and explicit PASS/FAIL/NOT RUN for every firmware/target case and each end-to-end gate.

Do not fabricate runtime markers to satisfy CI. The required marker is an observation emitted by a real target-owned runtime after the corresponding service has successfully started.
