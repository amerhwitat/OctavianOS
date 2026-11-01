#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${TMPDIR:-/tmp}/koronos-frame-allocator-test.$$"
trap 'rm -f "$OUT"' EXIT
"${CXX:-c++}" -std=c++20 -Wall -Wextra -Wpedantic \
  -I"$ROOT/kernel/include" \
  "$ROOT/tests/kernel/frame_allocator_test.cpp" \
  "$ROOT/kernel/core/frame_allocator.cpp" \
  -o "$OUT"
"$OUT"
"$OUT" above4g
