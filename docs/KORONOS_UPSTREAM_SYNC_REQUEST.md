# Koronos upstream sync request — 2026-11-05

This tracked request asks the scheduled source-sync workflow to import the latest public ChimeraIIOS main revision into the OctavianOS vendored snapshot.

Upstream repository: https://github.com/amerhwitat/ChimeraIIOS
Required upstream ref: main (resolve to the exact commit SHA at sync time)
Latest known upstream commit when this request was recorded: 20475db33afa5ec5c9423e10cfd97b1334386fda

## Required checks

- Update vendor/chimera-ii-os/UPSTREAM_REVISION to the exact imported commit.
- Enforce strict path and SHA-256 parity for the vendored source snapshot.
- Preserve Octavian-specific build-time artwork overlays outside the vendored source snapshot.
- Run native Koronos build, x86-64 boot checks, and the real Live/Installer/Recovery userspace handoff verifier.
- Do not publish a native ISO prerelease unless the production userspace verifier passes.

## Upstream kernel milestone

The upstream CR3 hardening commit saves and restores the actual active kernel CR3 around user entry, validates the physical root, and restores it on process exit and timeout. The full process context-switch integration, complete native VFS syscall dispatch, and process signal delivery remain outstanding.

## 2026-11-05 follow-up

The upstream follow-up also adds a catalog-only filesystem support classification
and a Linux x86-64 syscall translation regression test. The native syscall entry
now translates Linux x86-64 syscall numbers before dispatch, so Linux syscall
1 (write) cannot be confused with native Chimera syscall 1 (exit).

The translation currently covers only the implemented semantic calls. Linux
fork, execve, wait4, mount, signal, and other unimplemented operations remain
ENOSYS. This does not complete the process lifecycle or VFS and is not runtime
release acceptance.
