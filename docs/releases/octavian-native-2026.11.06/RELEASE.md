# OctavianOS — native Koronos ISO octavian-native-2026.11.06

| Field | Value |
| --- | --- |
| File | `octavian-native-amd64.iso` |
| Size | 41308160 bytes (39 MiB) |
| SHA-256 | `e477c8dbfe0dfa6b70ea38cd5901ff19234fcd2e6ce3fc667938fcaced71b86a` |
| Kernel | Koronos (Multiboot2 ELF64) + 373-entry embedded knowledge database |
| Boot | GRUB 2.12 hybrid BIOS + UEFI, menu waits 300 s for input |
| Targets | Live, Installer, Recovery (ring-3 init each) |
| Payload | media 57, apps 153, docs 278, CI workflows 83, catalogues 123 files |

## Menu behaviour
Primary menus (GRUB, Jasper, Spit Fire, Installation) now hold for **300 s** with a visible countdown;
sub-menus (recovery, safe mode, last-known-good, services) hold 120 s. Verified on serial:
`automatically in 300s` … `298s` with the kernel not starting.

Two real config bugs were fixed to make that true: GRUB script has no `||` operator and no `&&`
chains, so the previous config aborted while parsing and GRUB booted the default entry in ~7 s.

## Verification (2026-11-06, unchanged fail-closed verifier)
| target | BIOS | UEFI |
| --- | --- | --- |
| live | PASS | PASS |
| installer | PASS | PASS |
| recovery | PASS | PASS |

Traces in `traces/`. Each PASS: `[KRN ] KORONOS READY` → `[AI  ] Knowledge database staged: 373 entries`
→ CPL-3 `USER INIT SYSCALL` → `USERSPACE READY: target=<t> init_pid=<n>`.
