# Third-party SDK and toolchain policy

This directory holds provenance, version locks, build recipes and license metadata—not
unlicensed vendor SDK binaries.

- Open-source toolchains may be fetched at pinned versions and verified by checksum.
- Apple macOS/iOS SDK frameworks and headers are proprietary/licensed Apple materials.
  They must not be copied into Git or redistributed. Use an independently licensed local
  SDK via `APPLE_SDKROOT`; otherwise report that target as unavailable.
- Microsoft Windows SDK/WDK and Android NDK are similarly external, license-controlled
  developer dependencies.
- Cross-compilers are host tools; generated ELF/EFI files must be tagged by target ABI.

See `vendor/chimera-ii-os/source/sdk/third-party-sdk-manifest.json` when that
pinned snapshot includes the manifest, and `docs/PLATFORM_RUNTIME_INTEGRATION.md`.
