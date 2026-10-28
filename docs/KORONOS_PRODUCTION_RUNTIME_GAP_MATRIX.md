# Koronos production runtime gap matrix

**Status date:** 2026-10-28  
**Release decision:** BLOCKED — do not merge or publish a release from this candidate.

This document records observed evidence, distinguishes implemented source paths from runtime acceptance, and defines the evidence required to reopen the release gate. A source-contract test or ring-3 probe is not production acceptance.

## Latest observed CI evidence

- [Native build / full-ISO userspace acceptance](https://github.com/amerhwitat/OctavianOS/actions/runs/40716583891): `build-koronos` passed; the production userspace acceptance job failed.
- [Ring-3 probe matrix](https://github.com/amerhwitat/OctavianOS/actions/runs/40716583844): all six isolated probe jobs passed. Their job names explicitly mark them **not production**.
- The failed production job downloaded `octavianos-full-iso-qemu-trace` and ran `tests/migration/verify-userspace-handoff.py` for Live, Installer, and Recovery under BIOS and UEFI. All six cases failed with: `FAIL: missing production service readiness (init explicitly reported NATIVE INIT BLOCKED)`.
- The production workflow consequently skipped prerelease publication. This is the correct fail-closed outcome.

## Evidence classification

| Area | What current evidence supports | What remains unproven / blocking |
|---|---|---|
| Kernel and ELF build | Native build job passed on this run. | A successful build is not a successful userspace boot. |
| Target/firmware routing | Routing and source-integration checks passed in the previously observed runs. | Must still pass on the exact final candidate revision. |
| Ring-3 syscall probe | Six isolated probe jobs passed. | Does not prove a production init process can be scheduled, block, resume, or supervise services. |
| Root filesystem | Production trace exercises read access to a CPIO-backed rootfs marker. | Writable filesystem backend, mounted writable `/tmp`, and process-owned descriptor semantics are not proven. |
| Scheduler/process lifecycle | Scheduler source has task selection and pending cooperative actions. | This is not proof of scheduler-owned resumable CPU context/address-space switching; FORK/EXECVE/WAITPID lifecycle remains a blocker. |
| Services and desktop | No production-ready marker was accepted by the full-ISO verifier. | Real service providers, persistent supervision, and measured Aurora/Marine desktop health are absent or unproven. |
| Installer | Target path is exercised by the six-case workflow. | Install to storage, cold reboot, and verify persisted state. |
| Recovery | Target path is exercised by the six-case workflow. | Seed a known fault, perform repair, and verify the repaired postcondition. |
| SMP | No qualifying evidence in the cited runs. | Demonstrate AP startup and overlapping execution on at least two CPUs; sequential traces do not qualify. |
| Release artifact | No release was published by the failed workflow. | One immutable ISO digest, exact production init ELF hashes, all six passing traces, and independent verifier success. |

## Required implementation order

1. **Process execution:** implement architecture-correct saved CPU context, scheduler-owned task switching, address-space switching, safe interrupt/syscall return, and task lifecycle. Do not report YIELD success until a task can actually yield and later resume.
2. **Process syscalls:** implement and test the real process/descriptor ownership model and required FORK, EXECVE, and WAITPID semantics. Unsupported operations must return a truthful error.
3. **Writable VFS:** implement a writable filesystem backend and mount contract; exercise create/write/seek/read/stat/chmod/chown/truncate/close/rename/unlink/mkdir/rmdir through ring-3 descriptors, including writable `/tmp`.
4. **Service providers and supervision:** supply actual storage, security, logging, and graphics providers; start services under a persistent supervisor and verify restart/exit handling and the Aurora/Marine handoff from runtime health evidence.
5. **Installer and recovery:** test a real disk write followed by cold reboot and persisted-state verification; separately seed a recovery fault and prove the repair postcondition.
6. **SMP:** prove AP online state from hardware startup and capture overlapping work on two or more CPUs with synchronization that rules out sequential execution.
7. **Production acceptance:** build one immutable ISO; record its SHA-256 and exact production init ELF hashes; run Live/Installer/Recovery × BIOS/UEFI; require a genuine CPL3-originated syscall acknowledgement and the same nonzero init PID in readiness evidence; run the independent verifier unchanged.

## Release gate invariants

- Do not manufacture readiness markers, substitute test ELFs, weaken the verifier, or infer runtime behavior from source presence.
- Keep unsupported syscalls fail-closed and report the actual error.
- Do not merge or publish until every required production postcondition passes on the same immutable candidate.
- Record failed logs and artifact hashes so a failure is reproducible.

## Exit criteria

Release status may change from **BLOCKED** only when the seven-step sequence above has attached, reviewable evidence and all six production traces pass the unchanged independent verifier. Until then, this document and the draft PR are status records, not a release attestation.


## Runtime honesty correction (2026-10-28)

The compatibility syscall dispatcher previously returned success for `CHM_SYS_YIELD` after invoking a scheduler callback. That callback does not save and restore a task's CPU context or address space, so it was not evidence of a real yield. The dispatcher now returns `ENOSYS` until scheduler-owned suspend/resume exists, and `syscall_backend_honesty_test.cpp` asserts that the callback is not invoked and success is not reported.

Commits:
- `f8f84bf1db83d0c277df1a907d32cd4a8ff7542d` — fail closed for unsupported compatibility yield.
- `76a065e7be656f31dc93c685579be3036e8dc464` — regression assertion for yield honesty.

This correction removes a false-success path; it does **not** implement scheduler context switching and does not resolve the production release blockers listed above. CI results for these commits must be inspected before treating even this correction as validated.

## Recheck on the current PR head (2026-10-28)

PR #136 head at recheck: `ccec5a5df07e1eef2b395047a0c041af0ee73e30`. The native full-ISO workflow [40721412073](https://github.com/amerhwitat/OctavianOS/actions/runs/40721412073) completed with the freestanding Koronos build, ELF/Multiboot2 validation, QEMU kernel readiness, ISO composition, and target-routing smoke steps passing. Its separate **Verify real Live, Installer, and Recovery userspace** job failed at **Require actual user-mode init acknowledgement for every target**. Prerelease publication was skipped. This is a fresh confirmation that build/boot routing is not production readiness.

The isolated [ring-3 probe run 40721412276](https://github.com/amerhwitat/OctavianOS/actions/runs/40721412276) passed its probe job, including the source-contract regression and bounded timeout test. Its job is explicitly labelled **not production**; it does not override the failed full-ISO acceptance job.

The current head therefore still does **not** demonstrate all six production traces, real resumable scheduling, process creation/exec/blocking wait, writable ring-3 `/tmp`, persistent service supervision and desktop health, installer cold-reboot persistence, seeded-fault recovery repair, or AP-backed overlapping execution. The previous six-case `NATIVE INIT BLOCKED` evidence remains a valid known failure; no evidence found in this recheck supersedes it with a production pass.

**Action:** continue implementation in dependency order; keep PR #136 draft and unmerged; do not publish. The next full acceptance run must report the exact ISO SHA-256 and production init ELF hashes for every trace and pass the independent verifier unchanged.


## Failure detail from acceptance job 122938887014 (2026-10-28)

The failed job downloaded the trace artifact from run 40721412073 successfully (artifact digest `sha256:ebd0620934da649cc7c9915837153783f59d8465c03189674f4a335e536b3ad2`). It then ran `tests/migration/verify-userspace-handoff.py` for each target/firmware pair. All six cases returned the same explicit production failure:

```
FAIL: missing production service readiness (init explicitly reported NATIVE INIT BLOCKED)
```

The six failures were Live/BIOS, Live/UEFI, Installer/BIOS, Installer/UEFI, Recovery/BIOS, and Recovery/UEFI. The verifier exited 1; prerelease publication remained skipped. This is not a missing-artifact or download problem: the trace artifact existed, but its recorded runtime explicitly blocked readiness.

### Required implementation response

Do not change the verifier to accept `NATIVE INIT BLOCKED`, emit a synthetic readiness marker, or weaken the production gate. The first implementation milestone remains architecture-correct resumable execution: per-task saved trap/register state, owned kernel stack, address-space identity/lifetime, and a real context switch through the architecture entry/return path. Then implement process creation/exec/wait/reap and writable VFS/tmpfs with ring-3 syscall tests. Only after those primitives are real can init supervise production services and report readiness. Provider, installer, recovery, and AP/SMP work remain subsequent acceptance milestones.

The current session inspected the failed job logs and updated this evidence record; it did not implement or compile those runtime primitives. PR #136 remains draft/unmerged and release remains blocked.


## Latest revalidation on evidence-update head (2026-10-28 16:39 UTC)

The workflows triggered by evidence-update commit `76e9b5f545d49e426b7213074be3334e3f837efb` have now completed:

- [Native Koronos kernel build / full-ISO run 40727315297](https://github.com/amerhwitat/OctavianOS/actions/runs/40727315297): the freestanding kernel build, ELF/Multiboot2 checks, QEMU kernel marker, ISO composition, and target-routing smoke tests passed. The separate production userspace verification job failed.
- [Chimera source integration run 40727315299](https://github.com/amerhwitat/OctavianOS/actions/runs/40727315299): passed.
- [Boot target routing run 40727315262](https://github.com/amerhwitat/OctavianOS/actions/runs/40727315262): passed.
- [Ring-3 probe run 40727315085](https://github.com/amerhwitat/OctavianOS/actions/runs/40727315085): passed, but is explicitly not production acceptance.

The new full-ISO trace artifact (ID `12833841418`) downloaded and passed GitHub's SHA-256 digest verification: `sha256:a2368f0e6523f9bf81e42bc003ae9300f106422035baf6edd6f695e517edbe19`. The independent verifier then failed all six target/firmware cases with `FAIL: missing production service readiness (init explicitly reported NATIVE INIT BLOCKED)`. Prerelease publication was skipped. This reproduces the runtime blocker on the latest tested merge commit; artifact integrity and successful build/boot-routing steps do not change the acceptance result.

**Action remains unchanged:** keep PR #136 draft and unmerged. Do not weaken the verifier, manufacture readiness, or publish. The current source still does not implement architecture-owned resumable context switching, process creation/exec/blocking wait, writable VFS/tmpfs, persistent service supervision/providers, installer persistence, recovery repair postcondition, or AP-backed overlapping SMP. No runtime implementation or local build is claimed by this evidence update.


## Re-audit of failed production job (2026-10-28 19:00 UTC)

A step-level recheck of [full-ISO workflow 40727315297](https://github.com/amerhwitat/OctavianOS/actions/runs/40727315297) confirms the failure is in the production acceptance gate, not in kernel compilation or artifact transport:

- `build-koronos`: **success**. Native freestanding build, ELF/Multiboot2 validation, QEMU kernel readiness, ISO composition, target-routing smoke tests, and trace upload completed.
- `Verify real Live, Installer, and Recovery userspace`: **failure** at **Require actual user-mode init acknowledgement for every target** after downloading the traces successfully.
- `Publish prerelease only after userspace acceptance`: **skipped**.
- All six Live/Installer/Recovery × BIOS/UEFI cases remain failed because production init reported `NATIVE INIT BLOCKED`. The existing trace artifact digest remains `sha256:a2368f0e6523f9bf81e42bc003ae9300f106422035baf6edd6f695e517edbe19`.

This re-audit did not change the verifier or convert any non-production probe into acceptance evidence. The source-level implementation blockers remain: architecture-owned resumable task context and trap return; process creation/exec/blocking wait/reap; writable VFS and ring-3 `/tmp`; persistent service providers and supervision; measured desktop health; installer cold-reboot persistence; seeded-fault recovery; and AP-backed overlapping execution.

**Decision:** PR #136 remains draft and unmerged. No release is authorized. Do not remove native init's intentional fail-closed blocker until the required services and lifecycle are actually implemented. This commit records the step-level CI evidence only; it does not claim a runtime fix or local compilation.


## Recursive root-cause analysis of production acceptance failure (2026-10-28)

### Finding: the observed failure is the intended production-init refusal, not an artifact transport or firmware-specific failure

The production workflow downloaded the trace artifact successfully and then failed at “Require actual user-mode init acknowledgement for every target.” The checked source explains why the later readiness requirement cannot pass: `vendor/chimera-ii-os/source/kernel/userspace/native_init.c` has an unconditional production block after its rootfs read probe. It writes `NATIVE INIT BLOCKED: service supervision unavailable...` and invokes exit syscall 1 with status 78. There is no branch in this init that starts the missing services or emits `USERSPACE READY`. Thus the 0/6 result is deterministic from the current production init behavior, assuming this source-built payload is the one in the candidate.

### Causal chain

1. **The kernel build succeeds, but build success only validates compilation and boot entry.** The full-ISO job's successful build and module-routing steps do not establish a working userspace service lifecycle.
2. **Target launch can load and enter one user ELF, but this is a single-process launch path.** `target_launch.cpp` admits one ELF, loads it, binds its address space to one process record, marks it RUNNING, and calls `koronos_arch_enter_user(...)` directly. On return it tears down that one address space. This is not a persistent PID 1 service manager.
3. **The init reaches ring 3 and performs a real syscall handshake, but it does not become ready.** `native_init.c` first invokes `int $0x80`, asks GETPID, writes its PID diagnostic, then performs read-only OPEN/READ/CLOSE of `/etc/chimera/target`. Those steps may prove user entry and a read-only CPIO path, but they do not prove writable rootfs, service supervision, or desktop health.
4. **The source then explicitly refuses readiness.** After successful target-file validation, `native_init.c` unconditionally writes the service-supervision blocker and exits 78. The kernel only recognizes a `USERSPACE READY: target=... init_pid=...` marker after the CPL3 acknowledgement and matching PID diagnostic; the init never emits it. The independent verifier correctly fails rather than treating the CPL3 syscall or rootfs read as readiness.
5. **The missing runtime capabilities explain why the explicit block exists.** `process.h` labels admission as load-plan-only; lifecycle API exposes `waitpid_poll` and explicitly says it is non-blocking. `process.cpp` owns admission metadata, runtime binding and read-only CPIO descriptors, but does not provide real fork/exec/blocking wait/reap scheduling. `syscall.cpp` returns ENOSYS for YIELD, FORK, EXECVE and WAITPID; OPEN accepts only read-only flags. `vfs_cpio.cpp` exposes immutable archive reads and a single immutable root mount, not writable tmpfs/VFS operations.
6. **The scheduler is callback stepping, not a process context scheduler.** `scheduler.cpp` invokes task callbacks and applies requested READY/BLOCKED/EXITED state after the callback returns. It does not save/restore a suspended ring-3 register frame and address-space ownership per task. Its parallel API returns zero until real AP startup and independent per-CPU execution exist.
7. **The failure is shared by all six target/firmware combinations.** The unconditional init blocker is target-independent except for the embedded target name, and it is reached after BIOS/UEFI routing. Consequently Live, Installer and Recovery all lack the same required readiness postcondition; changing firmware routing or retrying artifact download cannot repair this cause.
8. **Publication skip is downstream and correct.** The release job depends on production acceptance. Since no trace contains the required userspace-ready marker and all six verifier invocations fail, publication is skipped by design. It is not a separate publication failure.

### Root-cause classification

- **Direct cause:** production `native_init.c` deliberately exits 78 after printing `NATIVE INIT BLOCKED`, without starting a supervised service tree or emitting readiness.
- **Architectural causes:** no scheduler-owned resumable CPU context/address-space switching; no complete process lifecycle; no blocking wait/wakeup; no writable filesystem backend; no persistent PID 1 supervision.
- **Downstream missing postconditions:** actual storage/security/logging/graphics providers, Aurora/Marine session health, installer persistence, recovery repair proof, and AP/SMP overlap.
- **Not the cause shown by this run:** artifact download failure, an unbuilt kernel, or evidence that BIOS alone or UEFI alone is broken. The observed evidence does not support those hypotheses.
- **Verifier assessment:** do not weaken it. Its diagnostic explicitly distinguishes `NATIVE INIT BLOCKED` from a missing user launch and is correctly rejecting an init that ran but refused to claim production readiness.

### Fix sequence tied to the causal chain

1. Implement and architecture-test a saved task context, owned kernel stack, address-space switch, and safe suspend/resume through syscall/interrupt return.
2. Integrate task scheduling with process creation, transactional exec, blocking wait/wakeup, exit/reap, and descriptor cleanup; only return success for operations that actually work.
3. Implement fault-safe user memory access and a mounted writable VFS/tmpfs (including writable `/tmp`); retain read-only CPIO as a boot source, not the complete rootfs contract.
4. Implement persistent PID 1 supervision and real storage/security/logging/graphics providers with observable health/failure/restart semantics.
5. Add target-specific installer persistence and recovery-repair postconditions; add a real Aurora/Marine handoff with display and input health.
6. Implement real AP startup and prove overlapping work on two or more CPUs.
7. Build one immutable ISO, hash the ISO and production init ELF, and run the unchanged independent verifier against all six BIOS/UEFI target cases.

No runtime implementation or local kernel build is claimed by this root-cause update. It records source-backed causes and evidence boundaries; the release remains BLOCKED until the actual prerequisites are implemented and tested.


## Architecture integration checklist: x86_64 user entry, TSS/IST, CR3, and scheduler return (2026-10-28)

This checklist narrows the first implementation milestone. It is an integration contract, not evidence that these mechanisms are implemented.

### 1. Establish the architecture invariants before adding a context switch

- **GDT/TSS:** confirm the active GDT contains a valid 64-bit TSS descriptor, that the TSS is loaded with `ltr`, and that the TSS storage remains mapped and alive. On each CPU, initialize that CPU's `RSP0` to the top of a dedicated, mapped kernel stack for the task that will enter from CPL3. Do not point multiple concurrently running CPUs at one mutable TSS or shared entry stack.
- **IDT:** audit every gate used by user execution. User-callable syscall gates must have the intended DPL and selector; exceptions and hardware interrupts must use valid kernel selectors and mapped entry code. Document which gates switch stacks automatically and which do not.
- **IST:** assign dedicated IST stacks only to exceptions that need an independent emergency stack (commonly double fault, NMI, and machine check where supported by the kernel's policy). Each IST stack must be mapped, aligned, per-CPU, and large enough for the worst-case entry path. Do not assume IST replaces a valid TSS/RSP0 for ordinary CPL3-to-CPL0 transitions.
- **Entry ABI:** document the exact register frame pushed by `INT 0x80`, exceptions, timer IRQs, and any `SYSCALL` entry. The hardware frames differ; normalize them in assembly before passing them to C/C++, and preserve the original user RIP, CS, RFLAGS, RSP, and SS where applicable.
- **Interrupt discipline:** specify whether interrupts are disabled during the sensitive transition and exactly when they may be re-enabled. Prevent timer preemption while a per-CPU current-task pointer, kernel stack, TSS.RSP0, and active address-space identity disagree.

### 2. Make the switch one coherent architecture operation

A scheduler decision alone is not a context switch. The architecture switch must save the outgoing callee-saved registers and resumable interrupt/syscall frame; select a valid incoming task; activate its address space; update the per-CPU current task and TSS.RSP0; then restore the incoming frame and return through the matching architecture return path. The implementation must define lock ownership and interrupt state across the entire sequence, and must never resume a task whose kernel stack or page-table root has been freed.

- **CR3/address-space contract:** each runnable user process must own or reference-count a valid page-table root. The kernel entry/return mappings, IDT/GDT/TSS, interrupt stacks, per-CPU data, and scheduler code/data needed after the CR3 write must remain mapped in every relevant address space. Validate user mappings and permissions before access; do not treat a numeric user pointer check as sufficient protection against a concurrent unmap.
- **TLB/PCID policy:** document whether PCID is enabled. If enabled, define tag allocation and invalidation rules; if disabled, still prove that CR3 writes and address-space lifetime are correct. No stale user translation may cross process ownership.
- **First entry:** initialize a new task's user register frame and user stack only after the ELF load is fully validated and committed. Enter CPL3 through the architecture's reviewed `iretq` path (or the repository's equivalent reviewed mechanism); never return through a frame shape that was built for a different gate.
- **Exit and faults:** process exit must not free the currently executing kernel stack or active page-table root. Switch to another valid context first, then release resources. Page faults and double faults must produce a bounded diagnostic path; failure to reach the diagnostic path is a boot blocker, not a pass.

### 3. Required incremental evidence

1. Static/compile checks for GDT/TSS descriptor construction, selector values, IDT gate types/DPL/IST indices, and entry-frame layout.
2. QEMU tests for CPL3 entry, syscall round-trip, timer interrupt from CPL3, and controlled user page fault; capture RIP, CS, RSP, CR2 where applicable, CPU ID, current PID, and active CR3 in diagnostics.
3. A two-task test that repeatedly yields and resumes with register canaries, independent address spaces, distinct kernel stacks, and a verified TSS.RSP0 change. The test must fail if callbacks merely run to completion.
4. Exit/reap and fault tests proving no active stack or page table is freed prematurely, plus invalid-user-pointer tests proving faults are contained rather than escalating to double/triple fault.
5. Only after those tests pass: implement fork/exec/wait/wakeup and descriptor lifetime, then writable VFS/tmpfs, service supervision, target-specific postconditions, and AP-backed SMP overlap.
6. Run the immutable full-ISO production matrix and unchanged independent verifier. The six target/firmware traces must bind to one exact ISO SHA-256 and the corresponding production init ELF hashes.

### 4. Stop conditions

Keep the production init exit-78 guard and release gate unchanged if any of these are missing: a real saved/restored context; valid per-CPU TSS and entry stacks; verified CR3/address-space lifetime; ring-3 fault containment; real process lifecycle; writable filesystem; persistent service supervision and provider health. A passing probe, source-contract test, QEMU kernel-ready marker, or target-routing smoke test is not a substitute for these postconditions.

This checklist does not claim the repository currently satisfies these requirements. The current full-ISO acceptance result remains 0/6, with prerelease publication skipped.


## Latest recheck — Native Koronos workflow 40738193386

**Observed at 2026-10-28 17:48 UTC.** This is newer than the earlier run referenced above.

- [Native Koronos kernel build / full-ISO acceptance](https://github.com/amerhwitat/OctavianOS/actions/runs/40738193386): `build-koronos` succeeded; the production verification job failed; prerelease publication was skipped.
- The production job downloaded artifact `octavianos-full-iso-qemu-trace`, SHA-256 `d0dbcbc317bf087b40cc443561ceccae1e7366a86fafcbbb136caadef24e1df2`.
- The unchanged verifier `tests/migration/verify-userspace-handoff.py` was run against all six trace paths: `acceptance-{live,installer,recovery}-{bios,uefi}/debugcon.log`. Every case failed with `FAIL: missing production service readiness (init explicitly reported NATIVE INIT BLOCKED)`.
- This confirms the failure is not a missing trace artifact or a kernel/ELF build failure. The current native init source explicitly prints the service-supervision blocker after its ring-3 syscall acknowledgement and read-only target-file validation, then exits with status 78. Removing that guard or adding a readiness string without working supervision would falsify acceptance and is not an acceptable fix.
- The ring-3 probe matrix remains non-production evidence; boot-target routing and source-integration checks do not substitute for full-ISO service readiness.

### Next implementation gate

Do not close this issue by changing verifier expectations or readiness strings. First implement and independently test the runtime prerequisites in the architecture and syscall contracts: resumable per-task trap/context state with a valid kernel stack and address-space switch; process-bound exit plus lifecycle-safe fork/exec/wait/reap; user-pointer validation and writable tmpfs/VFS descriptors; then a persistent PID 1 service supervisor that starts and checks real target services. Only after those components pass focused tests should the same immutable ISO be exercised through the unchanged six-case verifier. Installer persistence, recovery repair, and real multi-CPU overlap remain separate acceptance requirements.


## Architecture implementation audit — current source, not a readiness claim

The next code phase must integrate with the existing x86-64 entry ABI rather than add a parallel, unused context-switch path.

- `vendor/chimera-ii-os/source/kernel/arch/x86_64/user_entry.asm` currently installs one global `koronos_tss64`, one global `koronos_syscall_stack_bottom/top`, and one global `koronos_cpu_syscall_state`. `koronos_arch_enter_user` stores a single kernel continuation and bootstrap CR3 in that global state, writes the same global TSS.RSP0, then enters user mode. This is a single-active-user-continuation mechanism, not a per-task/per-CPU context model.
- The syscall entry saves a register frame on the shared syscall stack and returns to the same user context unless the process exits. The exit and timeout paths restore the single saved C continuation and bootstrap CR3. They cannot yet suspend task A, run task B, then resume task A with independent kernel stacks and address spaces.
- `vendor/chimera-ii-os/source/kernel/core/scheduler.cpp` tracks callback state and pending cooperative actions; it invokes task callbacks to completion rather than saving an interrupted CPU frame and switching to another task. Its serial-range API explicitly does not prove SMP.
- `address_space.cpp` provides an address-space backend and clone/validation operations, but having multiple page-table roots is not sufficient: the entry code, TSS.RSP0, kernel stack ownership, scheduler current-task identity, and CR3 must change as one reviewed transition. The implementation must not destroy the active address space or stack before switching away.
- The existing ring-3 probe matrix is useful for entry/return and timeout regression checks, but its own workflow labels it non-production. It must not be relabeled as a task-switch test until two independently initialized tasks actually yield/resume with register canaries and distinct stacks/CR3 roots.

### Required architecture API contract before implementation

Define and review a stable task context shared by C/C++ and assembly, with compile-time offset checks for every assembly-consumed field. It must capture the callee-saved kernel registers and stack pointer needed for a suspended kernel continuation; separately define the user trap frame and its origin/privilege metadata. The scheduler must only switch while executing on a valid kernel stack, with interrupts and locks handled under one documented protocol. A per-CPU structure must own the active task pointer, kernel entry stack, and TSS.RSP0; the selected task's address-space root and TSS stack must be installed consistently before any return to CPL3. First entry must use an initialized user frame; resumed entry must restore the saved frame, not restart the ELF entry. Timer/preemption may not interrupt an unsafe half-transition.

Implementation is incomplete until CI builds the kernel and QEMU tests demonstrate two-task yield/resume, preserved register canaries, distinct CR3 values and kernel stacks, correct TSS.RSP0 on entry, syscall round-trip, timer delivery, controlled user fault containment, and safe exit/reap. If the existing boot mappings do not keep all kernel entry/scheduler data mapped in each address space, that must be fixed before CR3 switching is enabled.

This audit intentionally adds no fake context-switch implementation and does not change the exit-78 guard or acceptance verifier. It records the concrete integration constraints found in the current source so the next runtime patch can be reviewed against the actual assembly ABI.


## Runtime code increment — cooperative continuation primitive (not production acceptance)

Commit `89b01736e425637c0d7743e2398d5ba9523cfe12` introduced `include/chimera/task_context.h` with a shared context layout and C/C++ compile-time offset/size assertions. Commit `8f1b60a4fcbbc0a08aa9cf1fa45e7998b35ed43f` added `koronos_arch_context_switch` to the existing NASM entry object; subsequent commits added host ABI compilation and incoming-context validation. The build script now compiles/runs `kernel/tests/task_context_abi_test.cpp` and requires the assembly symbol to be linked.

**Scope and limitations are explicit:**

- The primitive saves/restores the SysV callee-saved registers and kernel continuation RSP, validates the incoming RSP alignment, CR3 page alignment, and kernel stack top, updates a caller-supplied active-CPU TSS.RSP0 slot, and switches CR3 before resuming the incoming continuation.
- It assumes the caller supplies a valid per-CPU TSS slot, initialized continuation stack, CPU-local serialization, and kernel mappings shared by both roots. It does not allocate stacks, initialize a first-run trampoline, define/restore a complete interrupt/user trap frame, handle asynchronous preemption, or enforce task/process lifetime.
- The existing TSS in `user_entry.asm` is still global, and `scheduler.cpp` still dispatches callbacks to completion. The new primitive is therefore not yet connected to the production scheduler or the current single-user-init launch path. It is a real architecture primitive, not proof of resumable userspace tasks.
- The ABI test checks layout only. It does not demonstrate context switching, TSS stack selection, timer delivery, fault containment, or SMP. Those require an architecture/QEMU test harness and must remain outstanding until the test actually runs.
- The exit-78 native-init guard and unchanged six-case verifier remain mandatory. No production readiness or release status is inferred from this increment.

### Required next code gate

Implement and review first-run context construction plus task-owned stack allocation and destruction; expose the actual per-CPU TSS.RSP0 slot from per-CPU architecture state; connect the switch primitive to a scheduler that can suspend/resume tasks; then add QEMU two-task register-canary, distinct-stack/CR3, syscall/timer/fault and exit/reap tests. Only after that can the process lifecycle, writable VFS/tmpfs, persistent PID 1 supervision, and six-case production run proceed.


## Koronos service manager comparison and parallel-start groundwork

### Linux systemd model used as the reference

The design follows the documented systemd concepts, not an attempt to copy systemd's implementation wholesale:

- **Targets** group a boot goal (for example, a graphical session or multi-user console).
- **Requirement edges** and **ordering edges** are distinct. A service may be required without requiring serial startup; units with no ordering edge can be started concurrently.
- **Dependency graph jobs** are resolved as a transaction; ordering constraints are honored regardless of declaration order.
- **Service state and health** are not equivalent to a registration record. A unit becomes healthy only after its actual start path and health check succeed.
- **Failure/restart policy** is per unit, and critical failures must prevent the selected target from being reported ready.

References: [systemd boot process](https://freedesktop.org/software/systemd/man/latest/bootup.html), [systemd unit dependencies](https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html), [systemd targets](https://www.freedesktop.org/software/systemd/man/latest/systemd.target.html).

### New Koronos service-manager code

The current service registry previously validated a dependency graph and emitted one topological order, while `chimera_kore_bootstrap()` intentionally marked device, storage, security, logging, and Kore providers BLOCKED. It had no actual service process executor.

The new commits add:

- `chimera_service_resolve_waves()`: validates a bounded manifest (maximum 64 units), detects missing/null dependencies and cycles, and groups all currently eligible units into the same dependency wave. Independent units therefore occupy the same wave rather than being artificially serialized by declaration order.
- `chimera_service_transition()`: validates conservative lifecycle state transitions instead of accepting arbitrary state changes.
- `chimera_service_all_healthy()`: checks actual recorded RUNNING state for every requested unit; registration alone cannot satisfy the check.
- Hosted regression cases for parallel-ready wave grouping, complete dependency coverage, cycle rejection, and state-transition/health behavior.

### Explicit implementation boundary

This is **dependency/job planning groundwork**, not a claim that Koronos services now execute concurrently. The current scheduler runs a callback to completion and the kernel has not integrated a persistent service executor with real resumable process contexts, blocking waits, restart supervision, service-specific health probes, or AP-backed workers. The service-wave result gives a future executor the jobs it may dispatch concurrently; it does not itself run them.

The target-specific production service set also remains unimplemented as runnable providers. Live, Installer, and Recovery must each select a target manifest and pull in the correct service graph; desktop targets must add display/compositor/session dependencies. Until real providers and their health checks exist, the existing BLOCKED states and native-init exit-78 guard remain correct. Do not emit `USERSPACE READY` based on a resolved graph or planned jobs.

### Next required service-manager gates

1. Add target manifests for Live, Installer, Recovery, and installed desktop; distinguish required versus optional dependencies and ordering constraints.
2. Implement a persistent PID 1 supervisor using the real process create/exec/wait/reap APIs; start all jobs in each eligible wave without ordering edges between peers.
3. Add service start/stop/restart policy, exit-status capture, health probes, timeout handling, dependency failure propagation, and orderly shutdown.
4. Prove overlapping service execution with QEMU traces once resumable task contexts and AP workers are real.
5. Require target-specific service health, desktop session health, installer persistence, and recovery postconditions in all six production ISO traces.

No service was marked RUNNING by these changes, no service provider was fabricated, and no production readiness or release acceptance is inferred.
