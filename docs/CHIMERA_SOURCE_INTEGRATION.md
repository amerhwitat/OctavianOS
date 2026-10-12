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
| Vendored source | Source snapshot exists under `vendor/chimera-ii-os/source/` | Compare full file inventory and provenance against the source repository; import history separately |
| Hosted runtime | CI exercises host info, compatibility listing, ISA inventory, alias translation and a safe built-in | Test supported host OS/CPU matrix and packaging |
| Native toolchain | CI configures the vendored CMake project | Compile representative C/C++ artifacts and verify SDK/header install paths |
| Koronos kernel | Kernel and boot sources are vendored | Build the real kernel and verify its ELF, entry contract and Multiboot2 header |
| Boot/menu | Static routing contract workflow passes | Build ISO and boot the exact artifact in QEMU; capture serial/debugcon evidence |
| Live / Installer / Recovery | Target configurations and payload contracts are tracked | Prove each selected userspace process starts and emits a readiness marker |
| Aurora | Desktop assets/contracts are present in the source snapshot | Launch a real session and verify compositor, input, app-launch and safe fallback behavior |
| ISA backends | Architecture/ISA inventories and tooling are present | Execute official conformance suites per backend; never infer execution from catalog rows |
| Mobile / alternate architectures | Source and target contracts may be present | Build and boot per validated device/profile; x86-64 success does not prove ARM/mobile support |
| Release | CI source-level checks are available | Rebuild ISO from the destination commit, verify SHA-256, boot test and publish only verified artifacts |

## Full source history import

The separate history importer requires the repository secret `OCTAVIANOS_IMPORT_TOKEN` with Contents and Workflows write permission. Configure it in GitHub repository settings, then run the **Import ChimeraIIOS source history** workflow. Never put a token in a commit, issue, chat, or workflow log. The importer is intentionally designed to preserve source history on `chimera-import/*` branches instead of overwriting OctavianOS `main`.

## Canonical architecture flow

`Spit Fire → Jasper/GRUB → Koronos ELF → hardware/driver initialization → scheduler/runtime loop → live/recovery/installer userspace → Aurora`

Each arrow is a required handoff to validate, not evidence that the next stage already works.
