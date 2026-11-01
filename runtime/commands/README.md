# Octavian native command environment

This runtime owns a separate Octavian command-candidate registry. The importer reads the vendored, source-backed Chimera catalogs and writes `runtime/commands/native-command-candidates.json`. Exactly 15 allowlisted multicall commands are marked native by default; every other imported command is discovery-only and queued for RNN-assisted provider ranking and later tests. The RNN router is advisory and never executes unknown commands. A catalog row is not proof of an installed binary or feature parity.
