# Command and ISA catalogues

This directory mirrors the authoritative ChimeraIIOS command and ISA reference catalogues for OctavianOS runtime planning.

- `commands/chimera-command-list.json`: command names and platform namespaces.
- `commands/compatibility-binary-policy.json`: native/provider resolution rules; SS64 is a name/reference index, never a binary source.
- `commands/coverage.json`: command-by-platform implementation and binary verification inventory.
- `isa/isa_database.json`: 104 architecture-family rows and their currently catalogued verified-form counts.

## Binary policy

The shared Chimera multicall source implements 25 command names, with one source-built executable and symlink aliases. The mirrored catalogue contains 854 unique commands across 971 platform entries; the remaining 829 names require a real provider or must remain unavailable. Hosted Linux providers are not Koronos-native syscall implementations. The coverage inventory keeps repository binary status unverified until a target artifact is built and validated; it does not invent executables.

The CI matrix cross-builds and QEMU-user smoke-tests eight Linux userspace ABIs. This is not an eight-architecture Koronos kernel port. The current Koronos boot target remains x86-64. ISA rows with zero verified forms are catalogue/discovery entries only; rows with some verified forms are still partial and do not imply a complete assembler, decoder, emulator, JIT or OS port. Each architecture needs its own toolchain, kernel/runtime contract and conformance tests before support can be claimed.

## Provenance

Mirrored from the ChimeraIIOS integration branch. Upstream blob SHAs are recorded in `commands/coverage.json`.
