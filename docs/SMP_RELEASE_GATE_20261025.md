# OctavianOS SMP release gate — 2026-10-25

## Status: BLOCKED

OctavianOS must not claim production SMP readiness from scheduler CPU counts, sequential callback execution, static source contracts, or a kernel build alone. Its release gate inherits the real-SMP acceptance contract from the integrated ChimeraIIOS/Koronos kernel and must be proven on the exact OctavianOS candidate ISO.

The corresponding ChimeraIIOS source audit is available at:
https://github.com/amerhwitat/ChimeraIIOS/blob/0eb27d80c6c44b3684bf8971917e700413983310/docs/SMP_IMPLEMENTATION_AUDIT_20261025.md

## Required evidence before promotion

1. **CPU discovery:** bounded ACPI MADT/Multiboot discovery; validated unique APIC IDs; explicit discovered, startup-requested, online, and failed states.
2. **AP startup:** architecture-specific trampoline and INIT/SIPI or supported APIC startup path; per-CPU stacks and execution/interrupt state; AP-written online acknowledgements with timeouts.
3. **Independent execution:** each online CPU enters its own scheduling loop and owns its current task; affinity, wakeups, task migration, and teardown are synchronized.
4. **Concurrency proof:** two distinct CPU-bound tasks pinned to separate online CPUs; task and CPU identities recorded inside the task; monotonic start/end timestamps with overlapping intervals; repeated QEMU multi-vCPU runs and hardware evidence where available.
5. **Negative tests:** missing/malformed MADT, duplicate IDs, AP timeout, failed IPI, repeated startup, unavailable affinity CPU, wakeup races, lock contention, and AP failure during teardown must fail closed.
6. **Immutable artifact binding:** retain commit SHA, ISO SHA-256, firmware/emulator configuration, APIC IDs, serial trace, test results, and the production DAPS manifest together.

## Full release gate

SMP evidence is necessary but not sufficient. The same immutable ISO must also pass Live, Installer, and Recovery under BIOS and UEFI; prove real init-PID CPL3 syscall and file-I/O behavior; prove installer persistence after cold reboot; and prove the recovery repair postcondition. A workflow-contract test or boot smoke test cannot promote these capabilities to production-ready.

## Change-control rule

Do not merge, tag, publish, or approve release while any required production trace is missing or failing. Do not synthesize AP-online markers or treat serial execution as concurrent execution. Keep SMP status blocked until source implementation, build, boot, concurrency proof, negative tests, and artifact-bound DAPS evidence all pass.
