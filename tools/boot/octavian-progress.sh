#!/usr/bin/env bash
# Event-driven progress contract shared by installer, Live CD and installed boot.
# Only callers that observe a completed phase may advance progress; no timed fake progress.
set -Eeuo pipefail
STATE_DIR="${OCTAVIAN_PROGRESS_DIR:-/run/octavian}"
STATE_FILE="${OCTAVIAN_PROGRESS_FILE:-$STATE_DIR/progress.state}"
JSON_FILE="$STATE_DIR/progress.json"
MODE="${1:-status}"
mkdir -p "$STATE_DIR"
write_state() {
  local percent="$1" phase="$2" message="$3" status="${4:-running}"
  [[ "$percent" =~ ^[0-9]+$ ]] || { echo "percent must be integer" >&2; return 2; }
  (( percent >= 0 && percent <= 100 )) || { echo "percent outside 0..100" >&2; return 2; }
  phase="${phase//|//}"; message="${message//|//}"
  local previous=0
  if [[ -r "$STATE_FILE" ]]; then
    previous="$(sed -n 's/^percent=\([0-9][0-9]*\)$/\1/p' "$STATE_FILE" | head -n1)"
    previous="${previous:-0}"
  fi
  if [[ "$status" == running ]] && (( percent < previous )); then
    echo "refusing non-monotonic progress: $percent < $previous" >&2
    return 3
  fi
  local tmp="$STATE_FILE.tmp.$$"
  {
    printf 'percent=%s\n' "$percent"
    printf 'phase=%s\n' "$phase"
    printf 'message=%s\n' "$message"
    printf 'status=%s\n' "$status"
    printf 'updated_utc=%s\n' "$(date -u +%FT%TZ)"
  } > "$tmp"
  chmod 0644 "$tmp"
  mv -f "$tmp" "$STATE_FILE"
  local json_tmp="$JSON_FILE.tmp.$$"
  printf '{"schema_version":1,"percent":%s,"phase":"%s","message":"%s","status":"%s","updated_utc":"%s"}\n' \
    "$percent" "$(printf '%s' "$phase" | sed 's/"/\\"/g')" \
    "$(printf '%s' "$message" | sed 's/"/\\"/g')" "$status" "$(date -u +%FT%TZ)" > "$json_tmp"
  mv -f "$json_tmp" "$JSON_FILE"
}
case "$MODE" in
  start) write_state 0 "${2:-Initializing}" "${3:-OctavianOS initialization started}" running ;;
  phase) [[ $# -ge 4 ]] || { echo "usage: $0 phase PERCENT PHASE MESSAGE" >&2; exit 2; }; write_state "$2" "$3" "$4" running ;;
  complete) write_state 100 "${2:-Ready}" "${3:-OctavianOS userspace is ready}" complete ;;
  fail) write_state "${2:-0}" "${3:-Failed}" "${4:-Initialization failed}" failed ;;
  status) if [[ -r "$STATE_FILE" ]]; then cat "$STATE_FILE"; else echo "status=waiting"; exit 1; fi ;;
  *) echo "usage: $0 {start [PHASE MESSAGE]|phase PERCENT PHASE MESSAGE|complete [PHASE MESSAGE]|fail [PERCENT PHASE MESSAGE]|status}" >&2; exit 2 ;;
esac
