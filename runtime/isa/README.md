# Octavian native ISA and command-learning runtime

The import workflow creates and commits:

- `runtime/commands/native-command-candidates.json`: common and cross-OS command names, with the 15-command native allowlist separated from unresolved candidates.
- `runtime/isa/riscv-opcodes.json`: source-backed fixed-bit RISC-V encodings imported from a pinned upstream revision.
- `runtime/isa/universal-instruction-catalog.json`: legacy ISA rows plus imported forms, retaining explicit encoding and execution status.

The advisory routers use the vendored deterministic recurrent-state research module to rank candidates. It is **not a trained LLM**. It does not invent opcode semantics, mark forms executable, install providers, or run unknown commands. The native ISO build stages the catalog and routers into `/usr/share/octavian/{commands,isa}` and adds `octavian-learn-command` and `octavian-learn-isa` entry points.

Current acceptance separates catalog presence, encoding-source validation, decoder/interpreter support, conformance, native execution, and successful OS userspace boot. A successful catalog-import workflow is not proof that the full ISO reaches userspace-ready state.
