#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$ROOT/kernel/core/koronos.cpp"
for claim in \
  "Core storage/security/logging services active" \
  "Hardware discovery service started" \
  "Storage discovery service started" \
  "Initializing installer services in parallel" \
  "Service orchestration online"; do
  if grep -Fq "$claim" "$SOURCE"; then
    echo "FAIL: Koronos still overstates runtime state: $claim" >&2
    exit 1
  fi
done
grep -Fq "Storage/security/logging backends remain DECLARED, not RUNNING" "$SOURCE"
grep -Fq "no process-backed installer workers are connected" "$SOURCE"
echo "PASS: Koronos boot logs describe declared services and withheld installer execution accurately"
