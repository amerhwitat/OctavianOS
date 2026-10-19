# Native runtime acceptance — OctavianOS

Last updated: 2026-10-19

## Command and ISA catalogs

The import pipeline creates a source-backed ISA catalog and a command candidate registry. The latest validated import found 1,459 RISC-V encoding records across 141 files (zero source-fetch failures), 1,613 universal instruction forms, and 3,348 command entries (15 native allowlisted, 3,333 candidate-only).

A catalog row is not an executable implementation. The ISA router always reports `execution_allowed: false`; the separate RV32 machine tested-subset manifest describes Python simulator test evidence, not native x86-64 kernel execution or complete architectural conformance.

## Trained RNN and optional local LLM

The build trains `CHIMERA-CHAR-RNN-LM-1`, a small character-level vanilla RNN, using balanced samples from the command and ISA catalogs. The last successful training check used 400 sequences for two epochs and observed loss decrease from approximately 1.788 to 1.545, then successfully reloaded the model and checked score round-trip. This is an actual trained RNN language model, **not an LLM-scale foundation model**.

The optional `--llm` mode calls a separately installed OpenAI-compatible model server on loopback only. The adapter only reorders candidate IDs supplied by the caller, rejects invented IDs, and falls back to deterministic ranking. It never grants command execution or ISA support. Both routers queue unresolved queries for later review.

The trained model and runtime capability report are build artifacts and are staged into the Live/Recovery runtime. Python 3 is required for the current model scorer.

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
