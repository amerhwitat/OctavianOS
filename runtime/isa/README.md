# Octavian native ISA and command-learning runtime

The import workflow creates and commits:

- `runtime/commands/native-command-candidates.json`: common and cross-OS command names, with the 15-command native allowlist separated from unresolved candidates.
- `runtime/isa/riscv-opcodes.json`: source-backed fixed-bit RISC-V encodings imported from a pinned upstream revision.
- `runtime/isa/universal-instruction-catalog.json`: legacy ISA rows plus imported forms, retaining explicit encoding and execution status.

The ISO build now trains a small, auditable **character-level vanilla RNN language model** on a deterministic, balanced sample of the imported command and ISA catalog rows. It round-trip validates the weights, stages the model into installed and live-initramfs roots, and runs both launchers with `--rnn-model`. This is genuine local RNN language-model training, but it is **not an LLM-scale foundation model** and is not claimed to understand ISA semantics. The deterministic recurrent-state router remains the baseline; the trained model only reorders catalog candidates. It cannot invent opcode semantics, mark forms executable, install providers, or run unknown commands. The native ISO build stages the catalog and routers into `/usr/share/octavian/{commands,isa}` and adds `octavian-learn-command` and `octavian-learn-isa` entry points.

Current acceptance separates catalog presence, encoding-source validation, decoder/interpreter support, conformance, native execution, and successful OS userspace boot. A successful catalog-import workflow is not proof that the full ISO reaches userspace-ready state.


## Optional trained local LLM inference

Both candidate routers accept `--llm`. This invokes an independently installed OpenAI-compatible model server only when explicitly requested. Set `CHIMERA_LLM_BASE_URL=http://127.0.0.1:8080/v1` and `CHIMERA_LLM_MODEL=<installed-model-id>`. The endpoint is restricted to loopback; remote URLs are rejected. Returned IDs are validated against the candidate allowlist and can only reorder results. Malformed output or an unavailable model falls back to deterministic retrieval. No model weights are bundled or claimed to be trained by this repository, and no candidate can become executable from LLM output alone.


**Execution caveat:** the routers and wrappers are embedded in the ISO's Live/Recovery initramfs as source files and catalog data. The current initramfs is BusyBox-based and does not yet provide a verified Python 3 runtime or a functioning Koronos process/ring-3 handoff. The wrappers now fail with an explicit dependency message if `python3` is absent. Therefore embedding and passing the packaging checks is not evidence that these tools execute inside the current bare-metal OS.


## Verified ISA execution subset

The vendored `tools/isa/riscv_codec.py` and `tools/isa/rv32_machine.py` implement a documented RV32I-oriented encoder/decoder and Python machine subset. CI now exercises register ALU families, immediate ALU and shifts, signed/unsigned byte/halfword/word memory operations, branch conditions, jumps, traps, CSR and FENCE constraints. This is interpreter-level unit evidence only—not native Koronos execution or full privileged-spec compliance. Imported forms outside this tested subset stay `not-implemented`.

## Userspace release gate

A kernel-ready marker alone does not satisfy userspace acceptance. The native ISO workflow requires a nonzero init PID marker matching each target: `USERSPACE READY: target=live init_pid=N`, `target=installer`, and `target=recovery`. The current smoke traces have not yet proven all three; the fail-closed gate blocks release publication until they do.
