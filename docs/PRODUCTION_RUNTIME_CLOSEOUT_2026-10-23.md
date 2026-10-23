# Production Runtime Closeout — 2026-10-23


## Check/Plan/Do closeout loop — 2026-10-23

### Check: source-backed failures
- Production Live/Recovery initramfs is bounded-decoded and CPIO-validated, then extracted into an unpublished RAMFS staging tree. The launch path explicitly returns before ring-3 entry when a production payload exists because the staged rootfs is not mounted/published into a process-visible VFS. This is the direct reason those production cases cannot produce a real user-originated syscall/readiness handshake on this path.
- `kernel/userspace/native_init.c` is diagnostic-only by design. It performs an INT 0x80 acknowledgement attempt, requests kernel-owned PID, writes diagnostics, reports unavailable services, and exits 78. Do not relabel this as production init.
- Installer payload is a disk/image container and does not share the Live/Recovery CPIO extraction path; it needs a real installer execution and persistence test.
- Genuine AP startup and per-CPU scheduler workers are absent. CPU discovery is not CPU-online evidence; a loop over run_once() is serial, not SMP.
- No supported process-visible VFS bridge was found on the reviewed production branch; the expected standalone VFS source path returned 404. Do not invent an API or connect the 64-node/4-KiB legacy RAMFS as if it were production-capable.

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
