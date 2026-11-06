# Chimera II source integration in OctavianOS

## Runnable entry point

The vendored source snapshot is exposed through a stable OctavianOS entry point:

```sh
python3 tools/chimera/chimera-hosted info
python3 tools/chimera/chimera-hosted compat list
python3 tools/chimera/chimera-hosted isa
python3 tools/chimera/chimera-hosted desktop-info
python3 tools/chimera/chimera-hosted translate --mode windows ls
python3 tools/chimera/chimera-hosted run --mode linux -- echo "hello from OctavianOS"
```

On Windows, use `py tools/chimera/chimera-hosted ...` if `python3` is not available. The entry point forwards arguments without shell interpolation and uses the checked-in hosted runtime. The hosted runtime can report host details, inventory candidate ISA metadata, translate a limited set of command aliases, execute its built-ins, and launch compatible host executables.

## Integration boundary

This is a runnable hosted user-mode bridge, not a complete guest OS or a kernel port. In particular:

- It does not replace the host kernel, implement the Windows API, or emulate Linux syscalls.
- An ISA catalog match is not proof of a decoder, compiler backend, emulator, or conformance.
- A desktop-open bridge is not the Aurora compositor or a GUI-ready session.
- A successful CMake configure is not proof that every toolchain driver or SDK can compile a target.
- A staged Koronos ELF is not proof of a successful boot or userspace handoff.

## Migration status and gates

| Area | Current evidence | Remaining acceptance gate |
|---|---|---|
| Vendored source | The strict sync job passed exact path and SHA-256 parity against upstream revision `48a6a51f1fe39c8f7f23c29abef9e91c50ea4375`; the validated snapshot is proposed in PR #29 | Merge the snapshot PR after CI passes, then repeat parity checks against the latest upstream revision |
| Hosted runtime | CI exercises host info, compatibility listing, ISA inventory, alias translation and a safe built-in | Test supported host OS/CPU matrix and packaging |
| Native toolchain | CI configures the vendored CMake project | Compile representative C/C++ artifacts and verify SDK/header install paths |
| Koronos kernel | Kernel and boot sources are vendored | Build the real kernel and verify its ELF, entry contract and Multiboot2 header |
| Boot/menu | Static routing contract workflow passes | Build ISO and boot the exact artifact in QEMU; capture serial/debugcon evidence |
| Live / Installer / Recovery | Target configurations and payload contracts are tracked | Prove each selected userspace process starts and emits a readiness marker |
| Aurora | Desktop assets/contracts are present in the source snapshot | Launch a real session and verify compositor, input, app-launch and safe fallback behavior |
| ISA backends | Architecture/ISA inventories and tooling are present | Execute official conformance suites per backend; never infer execution from catalog rows |
| Mobile / alternate architectures | Source and target contracts may be present | Build and boot per validated device/profile; x86-64 success does not prove ARM/mobile support |
| Release | A development prerelease ISO candidate exists at [native-iso-baa635daf41d](https://github.com/amerhwitat/OctavianOS/releases/tag/native-iso-baa635daf41d), with ISO, checksum, and CI boot report assets | Treat it as a development candidate only; repeat build/checksum/boot validation after the snapshot is merged and verify each target before a stable release |

## Automated source inventory audit

The `source-inventory` CI job checks out the current public `amerhwitat/ChimeraIIOS` main branch beside the vendored snapshot and publishes a JSON comparison artifact. It compares relative paths and SHA-256 hashes and records the exact upstream revision. The initial audit found 40 missing paths and a later content audit found 1,019 differing files. The automated sync job then copied the upstream tree and passed strict path/hash parity against revision `48a6a51f1fe39c8f7f23c29abef9e91c50ea4375`; that snapshot is proposed in PR #29. The integration workflow's separate inventory job remains report-oriented so intentional changes can be reviewed; the dedicated sync workflow is the strict gate.

A SHA-256 match proves byte-level parity for the checked regular files at that revision. It does not compare Git history, prove semantic equivalence, or establish a native build or boot.

Run locally:

```sh
python3 tests/migration/test_chimera_source_inventory.py
python3 tools/migration/chimera-source-inventory.py \
  --upstream /path/to/ChimeraIIOS \
  --vendored vendor/chimera-ii-os/source \
  --output reports/chimera-source-inventory.json
```

Add `--strict` to fail on any missing path, extra path, or content hash difference after intentional divergences have been reconciled.

## Full source history import

The separate history importer requires the repository secret `OCTAVIANOS_IMPORT_TOKEN` with repository Contents and Workflows write permission (a classic PAT needs `repo` and `workflow` scopes). The source-sync workflow uses the same secret to create its PR because the initial run showed that repository Actions settings prohibit `GITHUB_TOKEN` from creating pull requests. Add the secret in GitHub Settings → Secrets and variables → Actions, then run **Import ChimeraIIOS source history** from Actions. Never put a token in a commit, issue, chat, or workflow log. The importer preserves upstream branches and tags under `chimera-import/*` instead of overwriting OctavianOS `main`.

## Canonical architecture flow

`Spit Fire → Jasper/GRUB → Koronos ELF → hardware/driver initialization → scheduler/runtime loop → live/recovery/installer userspace → Aurora`

Each arrow is a required handoff to validate, not evidence that the next stage already works.
