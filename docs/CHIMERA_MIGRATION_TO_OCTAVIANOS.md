# Chimera II OS → OctavianOS migration ledger

This ledger is deliberately a status register, not a claim that the full source tree has already been imported or that all listed subsystems work on OctavianOS.

## Migration rule

Keep the canonical boot chain: **Spit Fire → Jasper/GRUB 2 → Koronos ELF → hardware/driver initialization → scheduler/runtime → Live/Recovery/Installer userspace → Aurora Wayland Glass Desktop**. Marine Desktop is a separate desktop session. Do not flatten unrelated source repositories into the destination root; preserve source history and isolate vendored/imported source until licenses, build systems and ownership are reviewed.

## Priority import groups

| Source area | Destination area | Acceptance gate |
|---|---|---|
| `kernel/`, `include/chimera/`, `hal/`, `isa/`, `data/isa/` | `kernel/`, `include/octavian/`, `hal/`, `isa/`, `data/isa/` | Compile per architecture; kernel ABI tests; ISA records separately marked documented/encoded/decoded/executed/conformance-tested |
| `boot/spitfire/`, `boot/jasper/`, `boot/iso/`, `boot/splash/` | `boot/spitfire/`, `boot/jasper/`, `boot/iso/`, `boot/splash/` | GRUB parser, config graph, generated ISO payload validation and QEMU target matrix |
| `desktop/aurora/`, `desktop/aurora/assets/`, `desktop/aurora/assets/library/Init.mp4` | `desktop/aurora-wayland-glass/`, `assets/splash/` | Offline artwork manifest, license/provenance, branded video output, runtime progress sourced from actual initialization events |
| Installer and live/recovery user space | `apps/installer/`, `runtime/live/`, `runtime/recovery/` | Image/manifest/contract checks; no simulated success; QEMU installer/recovery smoke tests |
| `Mobile Microkernel/`, `kernel/core/microkernel.cpp`, `hal/mobile/`, `editions/mobile/`, `kotlin/mobile/` | `kernel/microkernel/`, `hal/mobile/`, `editions/mobile/`, `apps/mobile-companion/` | CMake/build tests; ARM64/RISC-V64 contract tests; emulator/device boot only claimed after measured runs |
| `src/chimera-command-compat/`, SQL engine, shells/terminals | `runtime/command/`, `apps/terminal/`, `apps/sql/` | command contract tests, isolated SQL test database, native and compatibility mode tests |
| Filesystem, RAID, swap, NCB, compilers/IDE, hypervisor, ISA tooling, watchdog, log rotation | `runtime/storage/`, `tools/binary/`, `tools/isa/`, `apps/developer/`, `services/` | component-by-component tests, not a bulk “complete” label |
| Other owned application repositories | `apps/imported/<repo>/` or independent packages | Repository inventory, license/security review, package manifests and per-app build tests |

## Current verified destination capabilities

- N-bit software arithmetic substrate with configurable width (default 8192 bits); not a complete 8192-bit physical CPU.
- Explicit GRUB/Jasper source-level target routes for Live Aurora, Live Marine, installer, recovery, diagnostics and safe graphics.
- A target payload contract and extracted-ISO validator.
- Aurora Wayland Glass Desktop and Marine Desktop browser layout prototypes; native app launch and compositor integration are not implied by those prototypes.
- This change adds an event-driven progress-state writer, an mpv OSD reader, a video rebranding script, and octopus boot artwork. These still require wiring into the generated ISO build and real runtime callers.

## Splash and progress contract

1. Import the original `Init.mp4` from ChimeraIIOS with provenance intact; never overwrite the source.
2. Run `tools/artwork/rebrand-init-video.sh <source> <output>` in an image that has ffmpeg and DejaVu Sans installed.
3. Package the output at the path specified by the artwork manifest and the OSD script alongside it.
4. Installer, Live CD and installed OS must call `tools/boot/octavian-progress.sh` (or its native ABI equivalent) only after observing real completed work. Progress cannot be inferred from time or menu echoes.
5. mpv loads `tools/boot/octavian-progress-osd.lua` to render the current percentage, phase and message over the video. Once userspace is ready, write 100/complete and stop the splash.
6. If mpv, video, progress file, font or GUI is unavailable, continue boot with a text/status fallback; splash failure must not block boot.

## Octopus boot artwork

`boot/splash/octavian-octopus-background.svg` is the canonical editable vector source. GRUB 2 generally needs a supported raster image for `background_image`; the ISO build must rasterize this SVG to PNG (for example with ImageMagick or librsvg), stage the PNG at `/boot/grub/octavian-octopus-background.png`, and verify it exists before enabling the background. Spit Fire and Jasper menu renderers need their own format-specific staging. SVG existence alone does not mean firmware or GRUB can render it.

## What remains unproven

- Full source histories and all app source files have not been merged into OctavianOS main. The token-gated import workflow preserves refs; it is not itself a code-porting or integration pipeline.
- No claim that the destination has every Chimera kernel, feature, application, or mobile/microkernel implementation.
- No full ISO build from this commit, no payload-validator report against a real ISO, and no QEMU logs proving every target starts.
- Koronos consuming the mode/desktop ABI, executing userspace ELFs, real SMP scheduling, desktop readiness, installer disk operations, recovery and mobile hardware bring-up require runtime tests.
- The splash scripts and artwork are added as source tools/assets, but the generated ISO does not yet automatically contain a rebranded video and rasterized octopus PNG unless the build is wired to run these steps.
