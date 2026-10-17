# ISA source refresh in OctavianOS

Run the convenience entry point from the OctavianOS repository root:

```sh
python3 tools/isa/refresh_isa_catalog.py --refresh
python3 tools/isa/refresh_isa_catalog.py --offline
python3 tools/isa/refresh_isa_catalog.py --self-test
```

The vendored ISO builder also accepts `--refresh-isa-catalog` and runs the
source refresh before the normal build. The refresh imports configured public
source indexes, merges source references, imports the pinned machine-readable
RISC-V opcode definitions, and regenerates a universal catalog with operand,
register, flag, memory, privilege, feature, exception, provenance, and explicit
native/compatibility mapping fields.

A catalog row is not proof of a working execution backend. Unknown semantics
stay unknown; `not-implemented`, `implemented-unverified`, and
`conformance-tested` remain separate statuses. Full ISA coverage for every
processor family still requires dedicated importers, semantics implementations,
and architecture conformance tests. This refresh does not claim universal
execution or exhaustive coverage.
