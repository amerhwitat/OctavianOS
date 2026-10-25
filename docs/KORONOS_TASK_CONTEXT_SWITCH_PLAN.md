# Koronos task context-switch and syscall-boundary implementation plan

Status: design contract only. This is not evidence that context switching is implemented or production-ready. Keep release gates blocked until runtime evidence passes.

## 1. Separate architectural frames

On x86-64, keep three distinct data structures:
- **SYSCALL frame**: the exact GPR/return-state layout created by the user-entry assembly; RCX/R11 semantics must match the SYSCALL ABI.
- **Cooperative kernel context**: callee-saved registers, kernel RSP, resume RIP, flags policy, address-space root, TLS state and owned FP/SIMD state.
- **Full trap/interrupt frame**: vector/error-code normalization and privilege-transition stack state needed to resume an arbitrary preempted execution.

Do not reuse a bootstrap-global frame for multiple tasks or treat a syscall frame as a scheduler context.

## 2. Task-owned PCB contract

Each task control block must own or safely reference:
- stable nonzero task ID and explicit lifecycle state (NEW, RUNNABLE, RUNNING, BLOCKED, EXITING, ZOMBIE, REAPED);
- kernel stack allocation and guard/ownership metadata;
- address-space object and root identity, with reference/pin accounting;
- architecture-specific saved context and first-run trampoline state;
- TLS/FS/GS policy and separately owned, correctly aligned FXSAVE/XSAVE state;
- scheduler links, wait queues, exit status, parent/reaper relation and cancellation state;
- per-task syscall accounting and bounded diagnostic identity (not a readiness claim).

A task must not become RUNNABLE until its stack, address space, entry context and ownership references are valid. Every transition must be checked under the scheduler's documented locking/interrupt policy.

## 3. x86-64 context-switch ABI

The existing proposed 104-byte cooperative context layout is:
- offsets 0..40: R15, R14, R13, R12, RBX, RBP;
- offset 48: RSP; offset 56: resume RIP; offset 64: RFLAGS;
- offset 72: CR3 root physical address (or a separately specified CR3+PCID representation, never an ambiguous mix);
- offset 80: FS base; offset 88: user GS base;
- offset 96: pointer to task-owned, 16-byte-aligned FXSAVE/XSAVE state.

The assembly switch accepts outgoing/incoming context pointers, saves the outgoing cooperative state, validates/switches to the incoming kernel stack and address space, switches task TLS and FP/SIMD state, and transfers to the incoming resume RIP. A first-run context enters a dedicated non-returning trampoline that establishes ABI stack alignment and calls a typed entry function. Preemption must save/restore the full trap frame instead of pretending it is a cooperative call.

Before assembly integration, specify:
1. CR3 root versus PCID encoding and address-space reference lifetime.
2. Shared kernel mapping policy, TLB shootdown and invalidation rules.
3. Kernel GS/per-CPU ownership; never restore user GS as kernel GS.
4. FS/GS switching mechanism and CPU-feature checks.
5. FXSAVE versus XSAVE, CPUID/XCR0 negotiation, alignment and isolation.
6. Interrupt enable/disable points and lock handoff; never switch while holding a lock the incoming task needs.
7. APIC/timer preemption and interrupt-frame normalization.
8. Exit-to-reaper switching before freeing the exiting task's stack or page tables.

## 4. Safe syscall and VM boundary

For every syscall, validate arithmetic and user-range policy before dereferencing. Validate and pin the complete range against the calling task's address space and required permissions before irreversible I/O. Use a fault-contained copy primitive to handle mapping races; unpin on every exit path. Never retain raw user pointers after syscall return, use user memory as a format string, or let failed copy-out silently consume input or advance file offsets.

Required negative cases include null/zero-length policy, canonical-boundary violations, overflow, cross-page spans, unmapped later pages, supervisor-only mappings, read-only output, stale roots, failed pin/unpin, and concurrent unmap attempts. For read, prove an invalid output buffer does not advance the VFS offset, then read the same bytes successfully into a valid buffer.

## 5. Implementation sequence

1. **ABI freeze**: compile-time size/offset assertions, assembly comments and disassembly checks; no scheduler integration yet.
2. **PCB ownership**: task-owned context/stack/address-space/TLS/FP-state lifetime; reference and teardown tests.
3. **Cooperative switch**: kernel-only A→B→A round trip with callee-saved-register and stack-alignment checks.
4. **First-run path**: new task trampoline, explicit failure/exit path, and reaper-owned stack reclamation.
5. **Address-space isolation**: distinct roots, mapping permissions, TLB invalidation and no cross-task user mapping leakage.
6. **Syscall return and preemption**: connect syscall/trap frames to scheduler policy without frame-layout aliasing.
7. **SMP**: per-CPU run queues/ownership, lock correctness, IPI/TLB shootdown and measured overlapping execution on at least two CPUs.
8. **Userspace lifecycle**: fork/exec/wait only after their individual semantics exist; supervisor must reap/propagate failures and never synthesize readiness.
9. **Production acceptance**: actual ISO hash plus six Live/Installer/Recovery × BIOS/UEFI traces, same nonzero PID for CPL3 syscall and target readiness, ring-3 OPEN/READ/CLOSE, writable /tmp, Aurora/Marine handoff, installer cold-reboot persistence, recovery postconditions, and two-CPU overlap.

## 6. Architecture boundaries

The 104-byte layout above is x86-64-specific, not a universal PCB ABI. Each architecture needs its own saved-register/exception frame, privilege-transition rules, interrupt return, TLS and FP/SIMD policy, memory-ordering rules, and boot-tested implementation. AArch64 additionally requires a real entry/vector implementation and 2 KiB-aligned VBAR_ELx; RISC-V requires privilege/trap and SATP contracts. Do not advertise an architecture as release-supported from a generic structure or compile-only fixture.

## 7. Required evidence and fail-closed rule

Require compile-time ABI assertions; disassembly review; cooperative context round trip; first-run trampoline; distinct-root isolation; TLS/FP isolation; safe reaping; syscall invalid-buffer offset test; interrupt/preemption tests; AP startup and overlapping execution; and production target/firmware traces. Unit fixtures, sequential traces, source-level checks, kernel probes, and readiness strings alone are not proof of runtime acceptance.

Until all applicable evidence exists, context switching remains an implementation plan and production release remains BLOCKED.
