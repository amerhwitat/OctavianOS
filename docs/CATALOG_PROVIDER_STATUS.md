# Command and ISA catalog mirror — OctavianOS

## Source of truth

OctavianOS vendors the canonical ChimeraIIOS catalog set under:

`vendor/chimera-ii-os/source/`

The live-image builder stages the catalog into:

`/usr/share/octavian/catalogs/`

The mirrored catalog includes the unified command list, compatibility-binary policy, runtime-provider map, ISA instruction database, ISA family catalog, world architecture registry, architecture backend metadata, terminal registry and shell registry.

## Current inventory snapshot (2026-11-09)

| Measure | Count |
|---|---:|
| Command namespace entries | 970 |
| Unique command names | 892 |
| Duplicate command names across namespaces | 78 |
| ISA architecture records | 104 |
| ISA instruction rows | 154 |
| ISA source references | 61 |
| Architecture records marked catalog-only | 75 |
| Architecture IDs with any instruction rows | 14 |
| Aurora terminal registry entries | 20 |
| Shell registry entries | 8 |

The historical "838 remaining" count is not directly reconcilable with this source snapshot. Use the canonical command list plus the generated per-command provider ledger rather than stale aggregate counts.

## Build-time evidence

The live-image builder now:

1. Generates the command runtime capability manifest from the mirrored canonical inputs.
2. Copies command and ISA catalog files into the guest rootfs.
3. Runs the non-executing command provider audit against the actual rootfs.
4. Stores command paths, SHA-256 hashes and ELF machine metadata in `command-catalog-provider-ledger.json`.

The ledger is evidence of observed provider presence only. It does not execute commands or claim semantic compatibility, option parity, security, ABI compatibility or conformance.

## Implementation boundary

The canonical command runtime manifest currently identifies 15 native Chimera command implementations; the native command namespace contains 90 entries. Remaining entries require a real provider, an explicit compatibility runtime or a native implementation. The 104 ISA records include 75 catalog-only entries; a catalog record is not an encoder, decoder, compiler backend or hardware boot implementation.

OctavianOS's current live ISO is a Debian/Linux-kernel live environment that renders its own desktop payload. It is not the native Koronos kernel release. The Koronos BIOS/UEFI userspace handoff, native filesystem, Installer/Recovery, X server and SMP gates remain separate.

## Upstream acquisition policy

- Prefer upstream source builds where a supported build recipe and target toolchain exist.
- Otherwise use verified distribution/provider binaries with source, version, architecture and license provenance.
- Do not create empty stubs or promote metadata entries into executable claims.
- For foreign architectures, require the correct target triple, ABI, sysroot and runtime; successful compilation alone is insufficient.
- DOS applications are staged only from explicit license-reviewed, redistributable, SHA-256-pinned and smoke-tested manifests.

## Related work

- Canonical source repository: https://github.com/amerhwitat/ChimeraIIOS
- Command/ISA audit: https://github.com/amerhwitat/ChimeraIIOS/blob/main/docs/research/COMMAND_ISA_PROVIDER_AUDIT_2026-11-09.md
- Linux reference baseline: Linux 7.3.3 stable, https://kernel.org/
- LLVM cross-compilation: https://clang.llvm.org/docs/CrossCompilation.html
