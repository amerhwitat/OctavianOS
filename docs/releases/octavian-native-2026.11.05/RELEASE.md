# OctavianOS — native Koronos diagnostic image (NOT A PRODUCTION RELEASE) octavian-native-2026.11.05

Diagnostic BIOS/UEFI image and trace bundle for Koronos bring-up. The logs show ring-3 probe payloads, not production Live, Installer, and Recovery environments. This artifact is **not accepted for production release**.

| Field | Value |
| --- | --- |
| File | `octavian-native-amd64.iso` |
| Size | 27322368 bytes (26 MiB) |
| SHA-256 | `2f694c56ed21b74ae2306cea64c0c16e7d2bd756f9004ebdbc433c3560a41bab` |
| Kernel | Koronos (in-tree kbuild), Multiboot2 ELF64 |
| Boot | GRUB 2.12 hybrid: El Torito BIOS + `efi.img` UEFI |
| Targets | `target=live`, `target=installer`, `target=recovery` |
| Knowledge DB | `/boot/ai/knowledge-db.json` — 269 entries |

## Boot trace contract

`[KRN ] KORONOS READY` → `[AI  ] Knowledge database staged: N entries, M bytes` →
`USER INIT SYSCALL: target=<t> init_pid=<n>` (CPL-3 proof) → `USERSPACE READY: target=<t> init_pid=<n>`
emitted by the payload itself. Traces in `traces/`, one per target and firmware.

## Verification status

<badge>NOT PRODUCTION ACCEPTED</badge>

The six files under `traces/` are diagnostic traces. Their presence does not prove
that all six boots used the exact ISO identified by the single SHA-256 above.
The repository does not contain a machine-generated manifest binding each trace
to that ISO hash and its firmware/target configuration.

| Case | What the trace actually demonstrates | Production result |
| --- | --- | --- |
| Live / BIOS | Ring-3 console probe; no graphical session | BLOCKED |
| Live / UEFI | Ring-3 console probe; no graphical session | BLOCKED |
| Installer / BIOS | Ring-3 dry-run; no block-device backend and no disk writes | BLOCKED |
| Installer / UEFI | Ring-3 dry-run; no block-device backend and no disk writes | BLOCKED |
| Recovery / BIOS | Ring-3 diagnostics probe; recovery initramfs handoff is withheld | BLOCKED |
| Recovery / UEFI | Ring-3 diagnostics probe; recovery initramfs handoff is withheld | BLOCKED |

All inspected traces report one logical CPU. None demonstrates AP startup or
measured concurrent execution. The Live traces explicitly say there is no
graphical session. Installer explicitly says it is report-only. Recovery says
the native recovery init ELF/runtime is not wired to the payload.

Accordingly, the table above supersedes any earlier summary in this file that
described the six cases as PASS. A probe readiness marker is not production
target readiness.

## What each target does

- **Live** — ring-3 text console session: banner, yield, tick count, exit.
- **Installer** — storage/plan dry-run report; no block backend exists in ring 3, so it writes nothing.
- **Recovery** — diagnostics report (syscall ABI self-check, ticks), exit.

The Aurora HTML desktop ships in the Linux live ISO, not in this native image.
See `docs/KORONOS_VS_LINUX_7X.md` (subsystem map vs Linux 7.3) and `docs/KNOWLEDGE_DB.md`.
