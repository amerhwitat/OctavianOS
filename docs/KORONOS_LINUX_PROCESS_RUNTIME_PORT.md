# Koronos process-runtime port: Linux parity and safety contract

Status: engineering contract / audit baseline. This document does not claim that the process runtime is production-ready.

## Why this is a dependency set

A runnable userspace process requires all of the following to agree on one ABI:

1. Physical frame ownership and reservation.
2. Page-table/address-space ownership and user mappings.
3. ELF loading into a not-yet-active address space, with rollback on every failure.
4. Per-CPU privilege-transition state (GDT, TSS, kernel stack, syscall entry state).
5. A process object that owns its address space, kernel stack, saved register context, PID and lifecycle.
6. A scheduler/context-switch path that activates the selected address space and kernel stack.
7. Syscall entry/return and user-memory validation bound to the currently running process.

Copying only a target launcher is unsafe: it can create references to memory-management and architecture state that does not exist or is not owned by the process.

## Linux comparison

| Area | Linux x86-64 design | Koronos port requirement |
|---|---|---|
| Physical memory | Boot-time memory discovery feeds the page allocator (buddy allocator), with reserved ranges and zones | Parse the Multiboot2 map with overflow-safe bounds; reserve low memory, kernel, boot info, modules, framebuffer/MMIO and allocator metadata; do not silently truncate usable RAM |
| Address spaces | Each process has an mm_struct; VMAs describe ranges and page tables implement mappings | A process-owned address-space object, explicit mapping metadata, supervisor/user and writable/executable permissions, teardown and rollback |
| ELF loading | execve builds a new image and commits only after successful setup | Validate all ELF headers/segments first; stage mappings in a new address space; reject W+X, overlap and overflow; commit atomically |
| User entry | Architecture entry code establishes privilege transition state and a user register frame | Per-CPU TSS/RSP0 and kernel stack; validated selectors, canonical user RIP/RSP, sanitized RFLAGS; iretq/sysret path with correct frame |
| Syscalls | Entry assembly switches to trusted kernel state; kernel validates user pointers and process context | One documented ABI; preserve all required registers; validate CPL3, active PID and CR3; copy user data through checked accessors |
| Scheduling | task_struct, saved context, scheduler and address-space switching | Saved trap/context state, kernel stack per task, atomic CR3 + stack switch, interrupt-safe run queues and explicit task states |
| Exit/wait | Task exit releases resources and parent wait observes completion | Idempotent process teardown, deferred freeing when address space is active, wait/exit status and PID reuse rules |
| SMP/TLB | Per-CPU run state, locks and TLB shootdowns maintain cross-CPU correctness | Per-CPU transition stacks, allocator/address-space locks, TLB invalidation/shootdown before freeing mapped frames |

Linux is a behavioral and architectural reference, not code to copy wholesale. Koronos may begin with a deliberately smaller feature set, but must state and enforce its limits.

## Candidate implementation hazards already identified

The existing candidate branch is useful as a source reference, but is not ready to merge unchanged:

- The bitmap allocator caps physical memory at 4 GiB and assumes allocated physical frames are directly identity-mapped.
- The address-space clone assumes a particular low identity-map shape and rejects higher-half mappings; page-table table frames are accessed as physical pointers.
- The user-entry path uses global transition state rather than a fully per-CPU task entry design.
- The launcher is a synchronous bootstrap launch, not a general scheduler-backed process lifecycle.
- Mapping failure paths must prove that partially allocated page tables, mapped frames and metadata are all rolled back exactly once.
- The current process admission path is not equivalent to a transactional execve.

These constraints must be resolved or explicitly bounded by boot-time validation before enabling the runtime.

## Required implementation order

1. Frame allocator: parse and validate all Multiboot2 memory-map records; reserve every boot-owned range; support physical addresses above 4 GiB or explicitly reject boot configurations that exceed the supported ceiling; test exhaustion, fragmentation, double-free and overlap.
2. Address-space backend: use a physical-to-virtual mapping abstraction rather than assuming every frame is identity mapped; create/destroy page tables; map/unmap user pages; enforce NX/W^X; implement rollback and TLB invalidation.
3. ELF integration: validate complete ELF image and segment overlap before allocating; map PT_LOAD segments and stack; zero BSS; copy file bytes; publish the image only after every operation succeeds.
4. x86-64 entry: define selectors and frame layout from the actual GDT/IDT/TSS; install per-CPU TSS and kernel stack; validate canonical addresses and flags; preserve ABI-required registers and handle faults safely.
5. Process ownership: bind PID, address space, kernel stack and saved context in one process object; activate CR3 and kernel stack together; never free an active address space.
6. Scheduler and syscalls: add real context switching, blocking/wakeup, exit/wait and process-bound user-copy; do not report readiness for a probe-only or synchronous path.
7. Verification: host unit tests, ELF malformed-input tests, fault-injection rollback tests, assembly ABI checks, QEMU BIOS+UEFI boot, and the six target/firmware acceptance matrix.

## Release policy

Keep native init fail-closed. Do not remove native-init exit status 78 or emit readiness markers unless the target process has actually executed in CPL3, completed the required syscalls, and its target-specific postconditions have been observed. A successful compile, source-presence test, or ring-3 smoke probe alone is not production acceptance.

## Vendored OctavianOS source audit (2026-11-01)

The OctavianOS vendored Koronos tree is ahead of ChimeraIIOS main in source integration: its canonical `kernel/build-koronos.sh` source list includes `frame_allocator`, `address_space` and `target_launch`, and it assembles and links `arch/x86_64/user_entry.asm`. This is source integration, not proof that the implementation is production-safe.

The vendored tree still carries the following constraints:

- `kernel/include/chimera/process.h` still defines `CHIMERA_PROCESS_LOAD_PLAN_ONLY`; the process record remains a load-plan structure rather than a scheduler-owned task with an address-space reference, kernel stack and saved context.
- `kernel/core/process.cpp` admits and records ELF metadata; the actual mapping and user-image preparation are performed by a separate loader/backend path.
- `kernel/core/syscall.cpp` has a native ring-3 syscall dispatcher for GETPID, WRITE and EXIT, but explicitly describes YIELD as a safe no-op while scheduler-owned address-space switching is absent. The compatibility dispatcher still rejects EXIT/GETPID without an active process context.
- `kernel/core/interrupt.cpp` exposes INT 0x80 at DPL3 (0xEE), with a saved-CS check and process-context acknowledgement. That gate is only as safe as the TSS, per-CPU entry state, active CR3/PID checks and fault handling behind it.
- `kernel/arch/x86_64/user_entry.asm` currently contains one global TSS, one global syscall stack and one global syscall-state block. It is a single-bootstrap-process transition path, not a multiprocessor-safe per-CPU entry design.
- The frame allocator is capped at 4 GiB; the address-space implementation accesses frame physical addresses through identity-mapped pointers and assumes a specific bootstrap page-table shape. Both assumptions need to be made explicit and enforced or removed before general memory configurations are accepted.
- The launcher is synchronous and tears down the address space after the initial user entry returns. This does not provide a general runnable task, preemptive scheduling, wait/parent semantics or safe concurrent process teardown.

## Cross-repository reconciliation rule

OctavianOS must not be treated as the unquestioned source of truth merely because it contains more files. Its vendored runtime is a reference implementation to harden. Port only after each dependency has tests and an agreed ABI, then keep the two source trees byte-identical for shared Koronos files (or replace the vendored copy with a pinned, verifiable submodule/snapshot manifest). The current divergence in `process.cpp` and `syscall.cpp` must be reconciled intentionally, not overwritten wholesale.

## Immediate safe gate

Until the allocator's physical-address ceiling and mapping model, page-table teardown/rollback, per-CPU entry state and scheduler-owned task lifecycle are fixed and verified, keep native init fail-closed and do not interpret a ring-3 smoke probe as production readiness.

## Frame allocator implementation sync (2026-11-01)

The vendored `kernel/core/frame_allocator.cpp` and `kernel/include/chimera/frame_allocator.h` have now been synchronized byte-for-byte with ChimeraIIOS PR #218. The change tightens Multiboot2 parsing, rejects usable memory above the current 4-GiB bootstrap ceiling instead of silently truncating it, reserves framebuffer ranges independent of tag order, and validates ownership on free.

The matching host test is vendored at `tests/kernel/frame_allocator_test.cpp`; `tests/kernel/run-frame-allocator-host-tests.sh` compiles and runs both the allocation/reservation scenario and the above-4-GiB rejection scenario. The vendored canonical `kernel/build-koronos.sh` invokes this runner before compiling Koronos.

This establishes source parity for the allocator implementation, public header and host test only. It does not establish parity for the rest of Koronos, and the 4-GiB ceiling remains a deliberate limitation pending a physical-to-virtual mapping design and wider-frame allocator.

The allocator now walks Multiboot2 module tags independently of the bounded module-classification registry, so every module payload is reserved even if the registry reaches its enumeration cap. The synthetic host test includes a module tag while the module-registry stub reports zero entries, verifying this independent reservation path.
