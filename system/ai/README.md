# Chimera AI Workspace

Local-first desktop AI integration for the Aurora and Marine desktops.

## Resource library

Select the directories you want indexed:

```sh
chimera-ai-workspace scan --root ~/Projects --root ~/Documents
```

The default JSON database stores metadata and SHA-256 hashes only. To opt in to storing small supported text files for retrieval, add `--include-text`. Hidden directories/files, credentials, tokens, private keys, browser profiles and caches are excluded. Nothing is uploaded.

## Local LLM chat

Install and configure a local Ollama model or llama.cpp model, then run:

```sh
chimera-ai-workspace chat --model <local-model>
```

For Ollama, `<local-model>` is the local model name. For llama.cpp, it is a local model file path; select the backend with `--backend llama.cpp`. The interactive chat retrieves matching excerpts from the local JSON database and supplies them as context. It is retrieval-augmented inference, not fine-tuning or automatic weight training. If the database contains metadata only, run the explicit `scan --include-text` command first.

The desktop launcher opens this local chat workflow. If no model backend or model is configured, it reports the missing local prerequisite rather than downloading one.

## CNN/RNN inference

ONNX Runtime supports local CNN/RNN-compatible models when `numpy` and `onnxruntime` are installed:

```sh
chimera-ai-workspace infer --family cnn --model ./model.onnx --input-npy ./input.npy --output ./result.json
chimera-ai-workspace infer --family rnn --model ./sequence.onnx --input-npy ./sequence.npy --output ./sequence-result.json
```

Models, tensors and datasets are user supplied. This is inference, not model training. Training requires a separately selected dataset, architecture, compute budget and output path.

The ISO packages the integration and runtime probes, not proprietary model weights or unavailable framework dependencies.


## Curated hardware and systems knowledge

The live ISO stages a source-attributed JSON knowledge database at `/usr/share/chimera/ai/hardware-systems-knowledge.json`, its JSON Schema, a validate/search/append command, and a small character-level RNN checkpoint trained during image creation. The corpus includes architecture profiles and references for x86, Arm, RISC-V, Power, LoongArch, SPARC, IBM Z and embedded families; compiler/assembler/linker workflows; ABIs and object formats; firmware; and PCIe, USB, NVMe, Virtio, networking, graphics, audio, input, sensor, storage and power drivers.

Validate and search the packaged corpus:

```sh
chimera-ai-knowledge validate --database /usr/share/chimera/ai/hardware-systems-knowledge.json
chimera-ai-knowledge search --database /usr/share/chimera/ai/hardware-systems-knowledge.json --query "NVMe DMA PCIe driver"
chimera-ai-knowledge append --database ~/.local/share/chimera-ai/knowledge.json --base /usr/share/chimera/ai/hardware-systems-knowledge.json --input reviewed-record.json
```

Appending requires a unique record ID and registered source references. The user database is a separate writable overlay; the ISO corpus remains immutable. Records are summaries with links to primary specifications, not redistributed copies of copyrighted manuals. New online material is untrusted until reviewed; no downloaded commands are executed.

The build trains and evaluates a small vanilla character-level RNN from the corpus and records its corpus SHA-256, loss history, held-out score and checkpoint round-trip. It is not an LLM. CNN inference remains available through ONNX when dependencies and a compatible model are installed; CNN training is not claimed because no labelled, licensed CNN task dataset is included. Local LLM/RAG chat does not fine-tune model weights. AI suggestions never authorize privileged operations or prove native Koronos support.

This payload is part of the Linux-kernel live edition and does not satisfy the separate native Koronos CPL3/VFS/SMP and six-case release gates.
