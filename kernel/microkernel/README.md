# OctavianOS microkernel port plan

This directory is the destination contract for the ChimeraIIOS microkernel implementation; it is not a claim that the runtime is implemented.

## Required components

1. Boot-time service registry with explicit dependency graph and failure policy.
2. Message-passing IPC with bounded messages, endpoint capabilities, sender identity and cancellation.
3. Per-process address spaces, privilege separation and guarded memory copy.
4. Driver services isolated from the core; restart and watchdog policy.
5. Scheduler integration with safe per-CPU state and documented interrupt/preemption rules.
6. Audit events and bounded local logs with rotation.
7. ABI compatibility adapters for the native runtime and supported Linux/Windows/macOS command/application modes.

## Acceptance

- Unit tests for message length/ownership, capability checks, malformed messages and service restart.
- Race/sanitizer tests on the host model.
- QEMU test that starts the service manager, launches at least two isolated services, exchanges IPC, kills one service and demonstrates recovery.
- No claim of genuine SMP unless two or more CPUs are observed executing concurrently and scheduler/interrupt state is per-CPU.
