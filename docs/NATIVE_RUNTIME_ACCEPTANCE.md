# Native runtime acceptance — OctavianOS

Last updated: 2026-10-19

## Command and ISA catalogs

The import pipeline creates a source-backed ISA catalog and a command candidate registry. The latest validated import found 1,459 RISC-V encoding records across 141 files (zero source-fetch failures), 1,613 universal instruction forms, and 3,348 command entries (15 native allowlisted, 3,333 candidate-only).

A catalog row is not an executable implementation. The ISA router always reports `execution_allowed: false`; the separate RV32 machine tested-subset manifest describes Python simulator test evidence, not native x86-64 kernel execution or complete architectural conformance.

## Trained RNN and optional local LLM

The build trains `CHIMERA-CHAR-RNN-LM-1`, a small character-level vanilla RNN, using balanced samples from the command and ISA catalogs. The last successful training check used 400 sequences for two epochs and observed loss decrease from approximately 1.788 to 1.545, then successfully reloaded the model and checked score round-trip. This is an actual trained RNN language model, **not an LLM-scale foundation model**.

The optional `--llm` mode calls a separately installed OpenAI-compatible model server on loopback only. The adapter only reorders candidate IDs supplied by the caller, rejects invented IDs, and falls back to deterministic ranking. It never grants command execution or ISA support. Both routers queue unresolved queries for later review.

The trained model and runtime capability report are build artifacts and are staged into the Live/Recovery runtime. [Download the latest validated model/catalog artifact](https://github.com/amerhwitat/OctavianOS/actions/runs/39183883232/artifacts/12156859541). Python 3 is required for the current model scorer.

## Real userspace readiness and release gate

`KORONOS READY` proves that the kernel reached its boot marker. It does **not** prove that an init program entered ring 3 or ran. ELF admission/load-plan generation alone is not process execution.

The separate `verify-userspace-handoff` job requires each Live, Installer, and Recovery trace to contain, in order:

1. `[KRN ] KORONOS READY`
2. `USER INIT SYSCALL: target=<target> init_pid=<nonzero>` — acknowledgement from a user-originated syscall after CPL 3 was established
3. `USERSPACE READY: target=<same-target> init_pid=<same-pid>`

The release job depends on all three checks and remains blocked if any target fails. Current kernel logs explicitly report that no executable ring-3 entry path is connected; until address-space mappings, privilege transition, syscall return/interrupt handling, process scheduling/exit, and target init are implemented and QEMU-tested, the real-userspace gate should fail and no release should be published. Do not fabricate readiness markers to satisfy CI.

## Current verified build boundary

- Kernel ELF compile and Koronos boot readiness: independently testable.
- Command/ISA import, RNN training, model round-trip, and host-side router smoke: tested in CI.
- ISO visual assets: native ISO job now validates the Octopus SVG renderer and checks the generated PNG in the final ISO.
- Live/Installer/Recovery module routing: boot-target smoke checks exist, but they do not establish actual userspace execution.
- Full application-by-application Python and Java conversion, GUI parity, and Windows executable packaging remain separate backlog items. Kernel, bootloader, and architecture-specific code remains native.


## Latest native ISO gate result

- [Native ISO build run](https://github.com/amerhwitat/OctavianOS/actions/runs/39183873609): the kernel build, RNN training/staging, Live/Recovery payload build, Octopus artwork render, final-ISO artwork inspection, recovery and installer routing smoke tests, full-ISO Koronos boot, and candidate artifact upload all passed.
- [Download the ISO candidate artifact](https://github.com/amerhwitat/OctavianOS/actions/runs/39183873609/artifacts/12157078393). This is an Actions artifact for review, not a published GitHub Release.
- The separate userspace gate failed closed for Live, Installer, and Recovery because their traces lacked both a user-originated init syscall acknowledgement and an actual init PID readiness marker. The prerelease job was skipped as intended.


## Status refresh — 2026-10-19 (run 39271192234)

The latest smoke matrix [#39271188845](https://github.com/amerhwitat/OctavianOS/actions/runs/39271188845) completed successfully for all six test-only ring-3 probe jobs. This is not production target acceptance.

The latest native build [#39271192234](https://github.com/amerhwitat/OctavianOS/actions/runs/39271192234) compiled Koronos, validated the Multiboot2 contract, passed module-classification tests and built Live/Recovery support payloads. It then failed closed because all required production init ELFs were missing from the staged ISO tree:
- `boot/live/user-init-live.elf`
- `boot/installer/user-init-installer.elf`
- `boot/recovery/user-init-recovery.elf`

The production validation step exited nonzero. Full-ISO boot/routing checks and real-userspace verification were skipped, and no ISO candidate was uploaded. Only the kernel ELF artifact was uploaded.

The audited source still has a load-plan-only process API, no verified CPL3 transition/TSS-backed kernel stack path, no user-originated syscall entry/return path, placeholder PID dispatch, and no AP startup. Therefore the missing ELFs must not be filled with smoke probes or marker-only stubs. Live→Aurora, install/reboot, real Recovery and AP-backed SMP remain NOT VERIFIED. Release remains BLOCKED.

## Cross-repository runtime parity update — 2026-10-19

The ring-3 runtime implementation already exercised by the OctavianOS test-only matrix has now been synchronized into ChimeraIIOS branch fix/production-init-elf-handoff-gate, including frame allocation/address spaces, native user-entry/TSS and syscall assembly, target-launch and module-routing code, interrupt/syscall integration, and build wiring. ChimeraIIOS now has its own six-case smoke-only workflow to validate that source parity; its results are pending and must be polled before claiming parity is tested there.

This is not production acceptance. The latest OctavianOS smoke run #39272210956 passed all six test-only probes. Native build #39272211204 still failed closed because the three real production target init ELFs are absent. The smoke payloads under kernel/tests/user_init_smoke.c must not be copied into production ISO locations. Live-to-Aurora, actual installation/reboot, real Recovery operation, and AP-backed concurrent SMP remain unverified; prerelease publication remains blocked.

## Chimera native build parity result — 2026-10-19

ChimeraIIOS native Koronos build run #39274513564 completed successfully after the runtime parity sync: ELF64 build, protected-process admission, ELF validation, and unresolved-symbol checks passed. The six-case smoke matrix in Chimera completed successfully at #39274699829; all six test-only probes passed. This is not production acceptance. This confirms native compile/link parity but not ring-3 runtime acceptance in Chimera or production service readiness.

### Latest native ISO attempt — 2026-10-19

Native Koronos build run #39274902857 again passed kernel compilation, Multiboot2 validation, QEMU kernel readiness, and Live/Recovery initramfs generation, then failed closed at production init ELF validation. The same three files are absent: boot/live/user-init-live.elf, boot/installer/user-init-installer.elf, and boot/recovery/user-init-recovery.elf. Full-ISO tests and prerelease were skipped. A newer docs-triggered native run #39275375884 is pending; do not infer success from it until completed.


## Root-cause audit — 2026-10-19 (native ISO run #39275559014)

The latest native build still fails at the production payload gate: [run #39275559014](https://github.com/amerhwitat/OctavianOS/actions/runs/39275559014). Kernel compile/link, Multiboot2 checks, QEMU kernel-ready probe, Live/Recovery initramfs generation, and six **test-only** ring-3 probes passed. The ISO builder then refused to continue because all three required files were absent. Full-ISO boot and the real-userspace verifier were skipped; no ISO candidate was produced.

The audit found the missing ELF problem is not just a path typo:

- `boot/iso/build-iso.sh` calls `verify-production-init-elfs.py` immediately after `prepare-layout.sh`, but there is no preceding production-init compiler/staging step.
- The GRUB Live/Normal/Recovery entries pass initramfs and JSON manifests, not a `chimera-user-init-elf` module. The Installer entry passes installer data/contracts but no target init ELF. The kernel's Multiboot classifier recognizes the init-ELF module kind, but the shipping menus do not currently provide it.
- The native user syscall surface currently covers GETPID, YIELD, TIME_TICKS, WRITE, EXIT and EXIT_GROUP. It does not provide the file read/open, mount/root-switch, exec/wait, device, or graphics/session interfaces needed to unpack/use the existing initramfs and start Aurora or perform a real installer/recovery workflow from ring 3.
- The existing shell `/init` scripts run inside cpio initramfs payloads; they are not the native ELF images the kernel's selected-user launcher consumes. Converting smoke probes or marker-only programs into these three files would create false production evidence.

Therefore the next implementation milestone is a coherent userspace ABI and service/runtime path (or a deliberately supported initramfs execution model), plus target-specific init sources/build/link rules and GRUB module routing. It must be followed by real QEMU traces for Live→Aurora, disposable-disk install→reboot, Recovery actions, and BIOS/UEFI × target acceptance. Until then the payload validator and prerelease gate must remain fail-closed.

Current verified boundary:
- Native kernel build and test-only ring-3 matrix: PASS.
- Production init ELF generation and routing: MISSING.
- Live→Aurora, install/reboot, Recovery operation, AP-backed SMP, six-case full production acceptance: NOT VERIFIED.
- ISO release: BLOCKED.
