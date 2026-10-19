# RNN/LLM chat adapter and production boot acceptance

## AI design
The repository's existing `tools/cognition/trainable_rnn_lm.py` is a small trainable character-level vanilla RNN for research and ranking; it is not a foundation LLM. `tools/cognition/koronos_chat.py` adds a bounded userspace chat client for a separately installed OpenAI-compatible inference server (for example llama.cpp). It does not ship weights, download models, execute generated text, or silently simulate answers.

Set `CHIMERA_LLM_ENDPOINT=http://127.0.0.1:8080/v1/chat/completions` and `CHIMERA_LLM_MODEL=<installed-model-name>`. Remote endpoints require HTTPS. An API key, if used, is read from `CHIMERA_LLM_API_KEY` and is never printed. Keep inference out of kernel mode.

References: Linux kernel docs https://docs.kernel.org/; Windows user/kernel isolation https://learn.microsoft.com/en-us/windows-hardware/drivers/gettingstarted/user-mode-and-kernel-mode; Apple XNU source https://github.com/apple-oss-distributions/xnu; llama.cpp inference runtime and MIT license https://github.com/ggml-org/llama.cpp. Review model-weight licenses separately. Do not bulk-copy Windows proprietary code or Apple/Linux kernel files without per-file license review.

## Six-case production acceptance
The contract enumerates Live/Installer/Recovery × BIOS/UEFI. Every case begins `NOT_RUN`. The Python validator checks only the evidence schema, not a boot. A case may pass only with real production ISO logs proving a CPL3-originated init syscall and matching nonzero PID READY event, with firmware, ISO/kernel hashes and attached logs. Live must start Aurora; Installer must complete, reboot and boot the installed system; Recovery must perform a real operation. Genuine AP-backed concurrent SMP remains a separate gate.
