# Production Runtime Closeout — 2026-10-23


## Check/Plan/Do closeout loop — 2026-10-23

### Check: source-backed failures
- Production Live/Recovery initramfs is bounded-decoded and CPIO-validated, extracted into RAMFS, mounted read-only at `/`, and paired with writable `/tmp`; the root pointer is published only after both mounts succeed. The current source therefore no longer supports the old blanket claim that the root mount is absent. The unresolved question is runtime proof: the production BIOS/UEFI trace must demonstrate successful mounts and ring-3 OPEN/READ/CLOSE plus tmpfs mutation. Installer still explicitly refuses launch until its storage-backed root namespace is mounted.
- `kernel/userspace/native_init.c` is diagnostic-only by design. It performs an INT 0x80 acknowledgement attempt, requests kernel-owned PID, writes diagnostics, reports unavailable services, and exits 78. Do not relabel this as production init.
- Installer payload is a disk/image container and does not share the Live/Recovery CPIO extraction path; it needs a real installer execution and persistence test.
- Genuine AP startup and per-CPU scheduler workers are absent. CPU discovery is not CPU-online evidence; a loop over run_once() is serial, not SMP.
- A process-visible VFS syscall bridge and bounded tmpfs self-test are now present in the reviewed source. Their source/contract tests do not establish that the full production ISO successfully executes those operations; raw CPL3 syscall traces are still mandatory. Do not infer installer persistence from tmpfs or read-only rootfs coverage.

### Plan: close blockers in dependency order
1. Implement a capacity-appropriate transactional extractor with canonical paths, duplicate/prefix conflict rejection, strict type/symlink policy, total-byte/entry limits, and rollback.
2. Implement atomic VFS root publication plus process-owned namespace/descriptors and validated user-buffer file syscalls.
3. Implement process exit/wait/reap and address-space teardown as one lifecycle contract.
4. Build target-specific production init/service programs; only emit readiness after required service health checks, tied to the same nonzero kernel-owned PID that issued a CPL3 syscall.
5. Implement real installer write/verify/cold-reboot/read-back and recovery repair/postcondition tests.
6. Implement AP discovery/startup, per-CPU state/worker startup and overlapping execution evidence before enabling multi-CPU scheduling.
7. Run unchanged production acceptance for Live/Installer/Recovery × BIOS/UEFI on the final ISO, archive raw traces and artifact hashes.

### Do: committed scheduler safety fixes
- OctavianOS commit `3ad50e4d8e1ddf951acb37ea89d2a84afe53637a` uses one scheduler-online CPU until AP startup exists.
- OctavianOS commit `c98483fe122cd9b5a4d5956d1d06190834d45351` makes the parallel-run helper return zero instead of misreporting serial iteration as concurrent work.
- ChimeraIIOS commit `bf7683a22fef0ac27ae6501e53b759b61f21574c` applies the same CPU0-only initialization rule.

### Validation: observed, not inferred
- OctavianOS boot-target routing workflow succeeded for the reviewed branch.
- OctavianOS bounded initramfs ingestion workflow succeeded for the reviewed branch.
- Explicit user ELF smoke and ring-3 candidate smoke were still in progress at the last lookup; source integration had a cancelled run and a later run queued. The newest scheduler helper commit had no workflow rows returned at the time of the check.
- These checks do not establish production rootfs mount, production service health, all six BIOS/UEFI cases, Aurora, persistence, recovery repair, or genuine SMP.

### Release decision
Keep ChimeraIIOS PR #187 and OctavianOS PR #120 (and parent production ELF bridge) draft. Do not publish a production release until all seven dependency-order gates above pass. Never weaken the verifier, synthesize readiness, or count queued/cancelled/unreported checks as passing.


## Follow-up implementation — vendored RAMFS root publication and read-only process file syscalls (2026-10-23)

The vendored Koronos target launcher and syscall ABI were synchronized from the ChimeraIIOS implementation:
- vendor/chimera-ii-os/source/kernel/core/target_launch.cpp: bounded CPIO extraction now produces a staged RAMFS tree, then publishes its root pointer atomically for Live/Recovery only after extraction succeeds. Installer remains fail-closed because the disk/image payload is not mounted here.
- Process-bound read-only descriptors are tied to the active PID. open accepts read-only flags only; read validates user memory against the active process CR3 and caps reads at 4096 bytes; close enforces descriptor ownership. Exit cleanup reclaims descriptors.
- Native OPEN/CLOSE IDs and OPEN/READ/CLOSE dispatch were mirrored. WRITE remains console-only; file mutation is not implemented.
- The vendored kernel/build-koronos.sh now requires the rootfs syscall bridge symbols at link validation.
- Added the missing vendored tools/tests/test_native_init_launch_gate.py regression test and extended it to require publication, user-buffer validation, and syscall routing. Service readiness wording is synchronized too.

Commits: 5763a347244e2ca928dd98a3ed77a6a638a53afb, d8d125ae161b8ebe45fde665b90dfd3309a0fe81, e88c56d3ca4101ea78f79e081161261f46203a3c, 6fdb0c7b605142d7ce3de59254b50616954a9a48, 63a5e62a4d4a393a5a88a7b95a9fad0c7f2abd4a, c9ce8d688018e247f97b6324f5ac94cbf799bffd.

Verification status: latest commit workflow lookups reported no runs, and no local build or boot test was executed in this session. These source changes are therefore unverified. This bridge does not complete general VFS mutation, service supervision, Aurora startup, installer persistence, recovery repair, AP-backed concurrent SMP, or the six-case full production acceptance matrix. Keep PR #120 draft and release publication blocked.


## Closeout gate tightened — ring-3 file-operation evidence (2026-10-23)

The DAPS gate is synchronized with ChimeraIIOS and now requires all six target/firmware cases to include rootfs_file_syscalls_verified=true and a non-empty rootfs_file_syscalls_evidence reference, in addition to process_visible_rootfs=true. This prevents pointer publication alone from counting as proof that ring-3 can open, read, and close a file. The source-contract test asserts that these fields remain required. The same gate is mirrored in the vendored source tree. No evidence has been generated for these new fields, so production release remains blocked.


## General VFS and mutable tmpfs implementation update — 2026-10-23

Mirrored the current ChimeraIIOS VFS and target integration into the vendored source. The new VFS provides mount routing, canonical traversal-rejecting paths, PID-bound descriptors, offset/seek, read/write/open/close, mutation backend hooks, read-only mounts, and mount-operation pins. A bounded mutable tmpfs implements create/write/truncate/mkdir/unlink/rename with per-file and total-byte limits and copy-then-commit content replacement.

The production target launcher mounts the validated Live/Recovery initramfs RAMFS as read-only / and a bounded writable tmpfs at /tmp; native ring-3 OPEN/READ/WRITE/SEEK/CLOSE use the VFS. Ring-3 mkdir/unlink/rename are deliberately not exposed until permission/ownership checks are implemented. VFS and tmpfs regression tests are registered in both the canonical build script and CTest. DAPS now requires raw tmpfs mutation evidence for both Live and Recovery across BIOS and UEFI.

Verification remains unestablished: no local compile was run, and the latest workflow lookup returned no runs. Installer persistent storage, a disk-backed filesystem, service supervision, Aurora handoff/health, Recovery repair postcondition, AP-backed SMP, and the six-case production acceptance matrix remain open. Keep this PR draft and release blocked until real build and production evidence pass.


## Ring-3 VFS self-test

The vendored fail-closed native init now exercises /tmp create + truncate + write + seek + read + close through the real native syscall dispatcher and emits NATIVE INIT VFS SELFTEST PASS only if byte counts and payload match. Failure is diagnostic and exits 78; the marker is not USERSPACE READY. Production services and the full acceptance gates remain blocked pending raw traces from the unchanged verifier.


## 2026-10-23 CI closeout — candidate/production boundary

- Corrected `.github/workflows/koronos-userspace-acceptance.yml` naming and job/artifact labels to explicitly say **Koronos Ring-3 Candidate Smoke (not production acceptance)**. The workflow boots candidate probe ELFs; its green result must never be counted as production Live/Installer/Recovery acceptance.
- Latest observed ChimeraIIOS checks passed for boot artifacts, desktop compatibility, structured ISO composition, and the Koronos contract/build jobs. These are build/structure/regression results only.
- Source audit confirms the production native init currently prints `NATIVE INIT BLOCKED` and exits 78 by design. Kernel launch explicitly rejects Installer because a storage-backed root namespace is not mounted. Therefore the production init is fail-closed, not service-complete; installer/Aurora/recovery service behavior is not implemented to acceptance level by those stubs.
- Remaining root causes: production service ELF behavior is not complete; installer disk-backed root and persistence path is absent; native init does not launch Aurora or perform recovery repair; AP startup/concurrent SMP evidence is missing. The current DAPS checker tests evidence fields and artifact hashes but does not itself produce boot evidence.
- Release remains blocked. Require current-head native build, six production BIOS/UEFI traces, real ring-3 filesystem traces, Aurora handoff, installer cold-reboot readback, recovery postcondition, and AP-backed concurrent SMP before release.


## Additional cross-repository audit — 2026-10-23

- ChimeraIIOS now has an additional explicit UEFI candidate handoff pass for Live/Installer/Recovery (`061643babf6827bcb46adc0ec70ac083fb749cd6`), in addition to its existing BIOS candidate pass. The logs are collected with the target trace artifact. This is candidate smoke coverage from reconstructed target payload ISOs, not proof of the six full production ISO cases.
- The native init remains intentionally fail-closed: after its VFS create/write/seek/read/close self-test it exits 78 because it does not start and supervise the actual target services. The kernel service manager's metadata/dependency state is not a substitute for process spawning, service health, or desktop readiness.
- Installer is still blocked by the explicit missing storage-backed root namespace. A module containing `installation.img` and metadata is not evidence of a mounted writable disk filesystem or cold-reboot persistence.
- The current workflow does not generate `build/iso/production-closeout-evidence.json`; therefore a release gate requiring that evidence must remain blocked until a real production harness produces raw traces and independent Aurora, persistence, recovery-repair, and AP-concurrency evidence. Do not manufacture evidence JSON from candidate smoke output.
- Chimera's DAPS and standalone verifier now accept the actual production target/component/PID marker. These parser fixes and the UEFI candidate test improve detection and coverage, but they do not complete the native runtime.

### Act decision

Keep both OS release candidates blocked. Next implementation work must provide process exec/wait and service supervision, a storage-backed installer filesystem plus reboot/readback, real ISO × firmware acceptance for all six target cases, verified Aurora and recovery outcomes, and AP-backed concurrent SMP. Latest fresh CI status for the Chimera workflow update remains unconfirmed by the available PR-run lookup.
