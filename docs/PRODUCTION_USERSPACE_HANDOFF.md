# Production userspace handoff — acceptance and integration contract

**Release decision: BLOCKED. Latest reviewed native Koronos run: [#39399407705](https://github.com/amerhwitat/OctavianOS/actions/runs/39399407705), commit `3ba18cb597d8521eb06f2544fccefc747f14302c`.** The freestanding kernel build, ELF/Multiboot checks, ISO candidate build, and all six target/firmware QEMU trace captures passed their build/smoke steps. The separate production userspace verifier failed all six cases because no target init reached the real readiness handshake. Prerelease publication was skipped.

## What the traces prove

For each of Live, Installer, and Recovery under BIOS and UEFI, the trace includes:
- Koronos kernel-ready marker;
- target-specific init dispatched into the user-mode launch path;
- user-originated syscall acknowledgement, validated by the CPL3 interrupt gate;
- native init diagnostic containing the target and a nonzero kernel-assigned PID;
- a native init fail-closed message stating required filesystem/process/device/graphics services are unavailable;
- userspace exit syscall and exit status 78, followed by an error for missing target-specific readiness.

Therefore the low-level entry/syscall/PID diagnostic chain is observed in this run, but **that is not proof that every ELF-loader, address-space, GDT/TSS, or return-path invariant is completely sound**. It is bounded evidence that the tested path reached user-mode code and completed these diagnostics. Production acceptance remains zero of six because the init did not become ready.

The latest verifier failure is explicit: `FAIL: missing actual init PID readiness marker` for all six traces. Do not weaken the verifier, synthesize a readiness line in kernel code, or treat a PID diagnostic as service readiness.

## Current acceptance matrix

| Target / firmware | CPL3 acknowledgement + PID diagnostic | Target init readiness | End-to-end |
|---|---|---|---|
| Live / BIOS | Observed | FAIL — services unavailable, exit 78 | BLOCKED; Aurora handoff unproven |
| Live / UEFI | Observed | FAIL — services unavailable, exit 78 | BLOCKED; Aurora handoff unproven |
| Installer / BIOS | Observed | FAIL — services unavailable, exit 78 | BLOCKED; disk transaction/reboot unproven |
| Installer / UEFI | Observed | FAIL — services unavailable, exit 78 | BLOCKED; disk transaction/reboot unproven |
| Recovery / BIOS | Observed | FAIL — services unavailable, exit 78 | BLOCKED; recovery operation unproven |
| Recovery / UEFI | Observed | FAIL — services unavailable, exit 78 | BLOCKED; recovery operation unproven |
| AP startup / concurrent SMP | Not demonstrated | Not applicable | UNPROVEN; trace reports one logical CPU |
| Release / prerelease | Not accepted | Not accepted | BLOCKED; prerelease job skipped |

## Implementation gaps and next work

1. **Production init instead of bootstrap.** `vendor/chimera-ii-os/source/kernel/userspace/native_init.c` is explicitly a fail-closed diagnostic bootstrap. It reports PID and exits 78. It is not the real service manager or production init.
2. **Live service stack.** Wire actual rootfs/initramfs mount and file access, process/service supervision, device access, graphics/display service, and the Aurora/compositor launch. Readiness must be emitted by the running Live init only after required services succeed.
3. **Installer service stack.** Wire storage discovery, partition/filesystem operations, an explicit confirmation boundary, durable install transaction and error recovery, bootloader setup, and a verified reboot into the installed target. Existing installer scripts/manifests alone do not prove these operations run inside native userspace.
4. **Recovery runtime.** The traces identify that no dedicated native recovery init ELF/runtime is wired to the recovery payload. Add and route a recovery-specific runtime; prove a real repair/diagnostic action and report its result.
5. **Kernel service contracts.** Audit the process-bound syscall ABI, filesystem/rootfs APIs, device access, service lifecycle, and safe error propagation. The compatibility syscall dispatcher is not a substitute for a process-bound production service runtime.
6. **SMP.** Add AP startup, per-CPU initialization, synchronization and genuinely concurrent scheduling tests. One logical CPU in QEMU traces is not SMP acceptance.
7. **Release evidence.** Generate functional evidence from the actual target executions (Aurora, installer/reboot, recovery operation, AP-backed SMP); never hand-author evidence JSON or infer success from marker strings.

## Verified checks on commit `3ba18cb597d8521eb06f2544fccefc747f14302c`

- [Source integration #39399407656](https://github.com/amerhwitat/OctavianOS/actions/runs/39399407656): PASS.
- [Routing contracts #39399407673](https://github.com/amerhwitat/OctavianOS/actions/runs/39399407673): PASS, including fail-closed verifier regression tests.
- [Splash/progress contracts #39399407620](https://github.com/amerhwitat/OctavianOS/actions/runs/39399407620): PASS.
- [Ring-3 smoke probes #39399407717](https://github.com/amerhwitat/OctavianOS/actions/runs/39399407717): PASS, but explicitly **not production acceptance**.
- [Native Koronos build and production verifier #39399407705](https://github.com/amerhwitat/OctavianOS/actions/runs/39399407705): build and ISO/QEMU capture steps PASS; production userspace verifier FAIL for all six; prerelease SKIPPED.

## Release policy

Keep [PR #85](https://github.com/amerhwitat/OctavianOS/pull/85) open/draft and the release blocked until all six production traces pass the unchanged verifier, Live reaches Aurora, Installer completes a real disk transaction and installed reboot, Recovery completes a real operation, and AP-backed SMP is separately demonstrated. A source change or smoke-probe success is not a substitute for execution evidence.
