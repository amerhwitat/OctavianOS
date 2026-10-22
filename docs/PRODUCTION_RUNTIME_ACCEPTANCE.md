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

- The target-specific native init binaries in `kernel/userspace/native_init.c` currently perform a CPL3 syscall acknowledgement, validate that the selected data payload exists, emit `USERSPACE READY: <target> init pid=<N>`, and exit. Their own source explicitly limits that marker to the native-init ABI milestone. They are ABI probes, not production init implementations: they do not mount the initramfs, start Aurora, run installer actions, or provide a recovery shell.
- The root cause is also visible in `include/chimera/syscall.h` versus `core/syscall.cpp`: the declared ABI includes READ, MMAP, MUNMAP, IOCTL, NANOSLEEP, WAIT, and ARCH_PRCTL, but the native dispatcher implements only GETPID, YIELD, TIME_TICKS, payload validation, WRITE, and EXIT/EXIT_GROUP. There is no supported open/read/mount/exec/process-supervision path for unpacking and launching the initramfs `/init`, and no demonstrated display-device/compositor API. The existing gzip/newc archive is validated by its envelope only; it is not extracted or executed. Adding a readiness string would hide this missing runtime rather than fix it.
- `core/koronos.cpp` currently logs explicit withheld states for Live, Installer, and Recovery when no supported target runtime is wired. These messages are release blockers and must not be treated as successful handoff.
- `core/scheduler.cpp` deliberately returns zero from `chimera_sched_run_parallel()`; its comments state that no AP workers enter the scheduler from independent CPUs. SMP is NOT RUN / FAIL until AP startup, per-CPU state, scheduler participation, and overlapping work on distinct CPUs are demonstrated.
- The acceptance workflow must fail closed if any withheld-handoff message is present or if the target-specific runtime readiness marker is absent. A green legacy ring-3 smoke run is evidence for the ABI probe only, not production target acceptance.
- Native Koronos build workflow run `39764511700` had no jobs exposed at the latest status inspection; its result is unresolved, not PASS.
- In acceptance run `39764511575`, Live/BIOS and Installer/UEFI completed and failed at `Boot and require userspace-originated readiness`; the other four cases were still in progress at the latest step-level inspection. The Live/BIOS raw trace confirms ordered ring-3 syscall/readiness for PID 1, then fails specifically because `USERSPACE TARGET READY: live component=aurora-session` is absent. Installer/UEFI additionally logs `graphical userspace is not running`, `install execution is not verified`, and `Installer handoff withheld`. These are production-runtime failures, not compiler or ISO-staging failures.

### Implementation work still required

1. Implement and test the missing syscall/runtime foundation (user-pointer validation and safe copy, file/open/read/write, archive extraction, VFS/mount, process create/exec/wait/exit and supervision). Do not expose a syscall ID as supported until it has a real implementation and tests.
2. Implement a native userspace init/runtime that consumes the selected target payload through that archive/VFS interface and reports service readiness only after the services actually start.
3. Live: mount and start the production initramfs, supervise the session, start the Aurora compositor/session manager, and prove the session is usable.
4. Installer: implement and execute a target-owned installer runtime, perform a disposable-disk installation, reboot, and verify the installed system boots.
5. Recovery: implement a target-owned recovery runtime and prove a repair shell can execute a harmless diagnostic command.
6. Storage: implement/verify a real persistent block backend and filesystem mount; write, flush, cold-reboot, reattach, and verify data.
7. SMP: implement AP startup/trampoline, per-CPU stacks/state and scheduler workers, then demonstrate overlapping work on at least two CPUs.
8. Capture commit and ISO hashes, raw logs, verifier output, and explicit PASS/FAIL/NOT RUN for every firmware/target case and each end-to-end gate.

Do not fabricate runtime markers to satisfy CI. The required marker is an observation emitted by a real target-owned runtime after the corresponding service has successfully started.


### Latest production acceptance evidence — run 39767666859 (2026-10-22)

The six-case workflow has now demonstrated the same production-runtime failure in Live/BIOS, Live/UEFI, Installer/UEFI, Recovery/BIOS, and Recovery/UEFI. Installer/BIOS was still running when this status was captured, so the matrix remains incomplete; do not report 4/6 as the final count or infer its result before completion.

The raw QEMU trace narrows the immediate cause beyond the older “no native init ELF was staged” diagnosis: this candidate ISO does stage a target-specific NATIVE USER INIT ELF module alongside the selected data payload. The kernel enters ring 3, the probe calls GETPID and payload validation, writes USERSPACE READY: <target> init pid=1, verifies a syscall round-trip, and then calls EXIT. The kernel confirms that this ABI smoke process exited. The verifier then fails because no target-owned production marker appears, e.g. USERSPACE TARGET READY: live component=aurora-session. The Installer/UEFI trace additionally reports graphical userspace is not running, install execution is not verified, and Installer handoff withheld.

Therefore the current immediate root cause is not BIOS-versus-UEFI routing, ELF compilation, or failure to enter ring 3. The supplied native init is still only a probe and exits before it consumes/extracts the selected initramfs, mounts a VFS, launches a real target init, supervises services, starts Aurora, performs an install, or opens a recovery shell. For Live/Recovery, koronos_target_validate_boot_payload() checks only the gzip/newc envelope; for Installer it checks required module presence and rudimentary JSON opening characters. Neither path starts the target runtime. The same missing runtime integration explains the shared failure across firmware modes.

Safe fix required: implement the native target runtime and supporting kernel contracts (archive parsing/decompression, bounded CPIO extraction, VFS/file operations, process create/exec/wait/exit and supervision, device/display services), then make the production launcher start the real target-owned init and emit each target marker only after the relevant service is actually running. Installer additionally needs a disposable-disk install/reboot proof; Recovery needs a working diagnostic shell; Live needs a usable Aurora session. Keep the current fail-closed verifier unchanged. A marker-only change, re-labeling the probe, or weakening the check is not a fix.

Related evidence: https://github.com/amerhwitat/OctavianOS/actions/runs/39767666859 and https://github.com/amerhwitat/OctavianOS/actions/runs/39767666880. The native build succeeded, but its downstream real-userspace verifier failed. Release remains blocked; no production ISO release is authorized by these results.
