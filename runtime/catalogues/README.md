# Command and ISA catalogues

This directory mirrors the authoritative ChimeraIIOS command and ISA reference catalogues for OctavianOS runtime planning.

- `commands/chimera-command-list.json`: command names and platform namespaces.
- `commands/compatibility-binary-policy.json`: native/provider resolution rules; SS64 is a name/reference index, never a binary source.
- `commands/coverage.json`: command-by-platform implementation and binary verification inventory.
- `isa/isa_database.json`: 104 architecture-family rows and their currently catalogued verified-form counts.

## Binary policy

The Chimera native multicall source currently implements 15 command names. They share one source-built executable plus aliases. Every other catalogued command requires a real provider or must remain unavailable. The coverage inventory marks all repository binary presence as unverified; it does not invent executables.

ISA rows with zero verified forms are catalogue/discovery entries only. Rows with verified forms are still partial; they do not imply a complete assembler, decoder, emulator, JIT, or OS port. A command binary for a target ISA must be compiled with that target's toolchain, checked for the correct object format and machine type, then exercised under native hardware or a validated emulator before it can be marked supported.

## Provenance

Copied from ChimeraIIOS main. Blob SHAs are recorded in `commands/coverage.json`.
