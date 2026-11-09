#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
APPLY="$ROOT/userspace/bin/aurora-profile-apply"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
RUNTIME="$TMP/run/profile"
CONFIG="$TMP/etc/profile"
CMDLINE="$TMP/cmdline"
mkdir -p "$TMP/run" "$TMP/etc"

run_apply() {
  AURORA_RUNTIME_PROFILE_FILE="$RUNTIME" \
  AURORA_PROFILE_FILE="$CONFIG" \
  AURORA_CMDLINE_FILE="$CMDLINE" \
    "$APPLY"
}

# An explicit bootloader profile wins over the baked-in default.
printf '%s\n' aurora > "$CONFIG"
printf '%s\n' 'BOOT_IMAGE=/vmlinuz aurora.profile=marine quiet' > "$CMDLINE"
run_apply
[ "$(cat "$RUNTIME")" = marine ]

# A runtime profile selected after login survives subsequent service restarts.
printf '%s\n' gates > "$RUNTIME"
printf '%s\n' 'BOOT_IMAGE=/vmlinuz aurora.profile=aurora' > "$CMDLINE"
run_apply
[ "$(cat "$RUNTIME")" = gates ]

# Without an explicit boot option, use the persisted profile.
rm -f "$RUNTIME"
: > "$CMDLINE"
printf '%s\n' jasper > "$CONFIG"
run_apply
[ "$(cat "$RUNTIME")" = jasper ]

# A malformed boot value cannot replace a valid persisted profile.
rm -f "$RUNTIME"
printf '%s\n' 'aurora.profile=unknown' > "$CMDLINE"
run_apply
[ "$(cat "$RUNTIME")" = jasper ]

echo "OctavianOS profile routing: boot override, runtime persistence and fallback passed"
