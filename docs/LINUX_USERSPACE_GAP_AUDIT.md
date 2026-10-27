# Linux Userspace Gap Audit — OctavianOS

**Audit date:** 2026-10-27  
**Status:** cross-OS engineering gap register; not a claim of Linux compatibility or release readiness.

## Scope and comparison baseline

OctavianOS desktop targets (Aurora and Marine) are product/session targets, not proof of an underlying Linux-compatible userspace. Linux userspace requires a syscall ABI, process/thread lifecycle, virtual memory, VFS and descriptor semantics, IPC/signals, scheduling, devices, networking, service supervision, and an operational userspace image. UI parity with macOS or Windows does not supply those contracts.

| Area | Linux userspace expectation | OctavianOS evidence / gap | Acceptance required |
|---|---|---|---|
| Kernel/runtime ownership | Explicit supported kernel ABI and userspace execution contract | OctavianOS integrates the Koronos boot/runtime path; booting the kernel does not prove target init execution | Identify the exact kernel commit and candidate ISO hash in every trace |
| Production init | Target-specific production ELF, target payload binding and genuine execution | Prior six-case traces reached kernel/init diagnostics but did not prove successful target readiness; native init withholds readiness when dependencies are unavailable | Real init ELF in each ISO, CPL3 execution, user-originated syscall and matching nonzero PID |
| Process lifecycle | create/exec/wait/exit/reap, unique process identity and safe teardown | Must be verified against the selected Koronos revision; do not infer support from syscall names or a loader probe | Parent/child, exec replacement, exit status and reaping tests |
| VFS / files | Mount/root publication, descriptor operations, permissions and writable temporary space | Initramfs/image presence is not proof that the target root is visible to userspace | Ring-3 OPEN/READ/CLOSE, writable `/tmp`, rootfs and permission tests |
| Service supervision | PID 1 starts real services, checks health, enforces dependencies and shuts down | Service registry metadata does not prove that services are running | Real launch, health, restart/rollback and shutdown postconditions |
| Scheduler / SMP | Runnable processes execute; multiple CPUs start and overlap work | A sequential trace or CPU count alone is not SMP proof | AP startup plus overlapping work on at least two CPUs |
| Storage / installer | Durable writes, sync, reboot and read-back | Installer selection or UI is not an installed OS | Install to a test disk, cold reboot, verify persisted content and boot target |
| Recovery | Actual repair operation with verified postcondition | Recovery menu/module presence is not repair proof | Corrupt a disposable image, repair it, then independently verify the result |
| Desktop/session | Session manager, compositor, display and input services, app lifecycle | Aurora/Marine assets and launch panels are not proof of operational desktops | Session health, display/input, launch/close app and failure recovery |
| Compatibility | Native ABI or a tested Linux compatibility layer | Do not imply Linux application compatibility from a desktop resemblance | ABI conformance evidence or explicit unsupported/not-tested declaration |
| Publishing | Reproducible artifacts with test evidence and provenance | A successful web preview or package build is not OS release acceptance | Publish only exact artifacts whose production gates pass |

## Required release gates

- [ ] All six production cases: Live/Installer/Recovery × BIOS/UEFI.
- [ ] Each trace binds the exact candidate ISO SHA-256 and the production init ELF SHA-256.
- [ ] Same nonzero PID for user-originated CPL3 syscall acknowledgement and readiness.
- [ ] Rootfs/VFS and writable `/tmp` verified from the real user process.
- [ ] Installer cold-reboot persistence and recovery repair postcondition.
- [ ] Aurora/Marine session health verified independently of visual assets.
- [ ] AP-backed overlapping execution on at least two CPUs.
- [ ] No readiness markers synthesized by shell scripts or test probes.
- [ ] Publishing workflows preserve artifacts and diagnostics on failure and fail closed.

## Compatibility statement

Until a Linux syscall ABI or compatibility layer and its conformance suite are implemented, classify Linux application support as **not established**. Keep native OctavianOS apps and Linux-compatible apps distinct in the catalog, and label unsupported/not-tested states explicitly. Do not publish an OS release merely because the website, artwork, ISO composition, or kernel build succeeds.


## systemd comparison: kernel, manager, units and targets

Linux and systemd are separate layers. The Linux kernel provides process/thread and memory primitives, scheduling, syscalls, VFS, device and networking interfaces. systemd runs as userspace PID 1 and manages service processes, dependency ordering, readiness, restarts and shutdown. Units include services, sockets, mounts, devices, timers, paths, slices/scopes and targets. Kernel modules/drivers are not the same thing as service units. Targets are dependency/synchronization groups—not executables and not proof of health.

Koronos should follow that separation, but should not claim full systemd compatibility unless it implements the unit formats and behavior:

1. The kernel must supply real process creation/exec/exit/reap, scheduling, address spaces, safe syscalls, VFS and device interfaces.
2. A real userspace PID 1/service manager must launch actual executable images and track process identity and exit status. Registry entries alone do not start services.
3. Service descriptors should declare ID, executable, arguments, dependencies, target membership, criticality, restart budget, readiness probe, shutdown policy and security/resource constraints.
4. Validate unknown, duplicate, self-referential and cyclic dependencies; launch dependencies first; wait for readiness; roll back newly started services if a critical dependency fails.
5. Runtime states must reflect observed behavior. RUNNING/READY requires successful process launch plus a passing health/readiness check; registration alone must never set it.
6. Targets should aggregate required services and explicit postconditions. `live.target`, `installer.target`, `recovery.target`, and `graphical.target` are proposed Koronos concepts, not a claim that these targets exist today.
7. Keep object types distinct: Multiboot2 boot module, loadable kernel driver/module, and userspace service executable have different loaders, validation and lifecycles.
8. Test dependency ordering/cycles, launch errors, readiness timeout, unexpected exit/restart budget, shutdown ordering, duplicate instances, and critical-service rollback.

## Proposed Koronos service/target contract (design, not implemented behavior)

- A real production init process runs as PID 1 through the supported user-mode entry path.
- Each target manifest binds a target ID to validated service descriptors and required health postconditions.
- Every READY service has a tracked process identity and a successful configured readiness check.
- A target is READY only when all required services are READY and target-level postconditions pass.
- Logs include monotonic timestamp, target/service ID, PID, transition, exit status, restart count and failure reason.
- Missing executable, invalid manifest, dependency cycle, failed required service, timeout, or missing display/storage capability prevents readiness and returns a useful diagnostic.
- Unit tests are necessary but insufficient: production release verification must observe these transitions in the booted candidate ISO.

The existing registry/dependency planner is not a systemd-equivalent manager until process launch, health monitoring, restart/shutdown, and target postconditions are implemented and tested.
