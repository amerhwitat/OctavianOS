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
