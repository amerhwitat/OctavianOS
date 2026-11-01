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

OUT_PHYSMAP="${TMPDIR:-/tmp}/koronos-physmap-test.$$"
trap 'rm -f "$OUT" "$OUT_PHYSMAP"' EXIT
"${CXX:-c++}" -std=c++20 -Wall -Wextra -Wpedantic -Werror \
  -I"$ROOT/kernel/include" \
  "$ROOT/tests/kernel/physmap_range_test.cpp" \
  "$ROOT/kernel/core/physmap.cpp" \
  -o "$OUT_PHYSMAP"
"$OUT_PHYSMAP"
