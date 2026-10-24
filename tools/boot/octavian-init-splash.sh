#!/usr/bin/env bash
# OctavianOS Init.mp4 splash; progress is read from real init/service events.
set -Eeuo pipefail
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: octavian-init-splash [--background|--foreground]"
  exit 0
fi
MODE="${1:---foreground}"
VIDEO="${OCTAVIAN_INIT_VIDEO:-}"
for candidate in "${VIDEO:-/nonexistent}" \
  /boot/splash/Init-OctavianOS.mp4 \
  /usr/share/octavian/boot/Init-OctavianOS.mp4 \
  /usr/share/octavian/boot/splash/Init-OctavianOS.mp4; do
  if [[ -n "$candidate" && -s "$candidate" ]]; then VIDEO="$candidate"; break; fi
done
[[ -n "$VIDEO" && -s "$VIDEO" ]] || { echo "OctavianOS splash: Init.mp4 unavailable; continuing text boot." >&2; exit 0; }
PROGRESS="${OCTAVIAN_PROGRESS_FILE:-/run/octavian/progress.state}"
OSD="${OCTAVIAN_PROGRESS_OSD:-/boot/splash/octavian-progress-osd.lua}"
MAX_SECONDS="${OCTAVIAN_SPLASH_MAX_SECONDS:-30}"
PID_FILE="${XDG_RUNTIME_DIR:-/run}/octavian-splash.pid"
if [[ "$MODE" == "--background" ]]; then
  nohup "$0" --foreground >/dev/null 2>&1 </dev/null &
  exit 0
fi
read_percent() {
  [[ -r "$PROGRESS" ]] || { printf '%s' '-1'; return 0; }
  local value
  value="$(sed -n 's/^percent=\([0-9][0-9]*\)$/\1/p' "$PROGRESS" | tail -n 1)"
  [[ "$value" =~ ^[0-9]+$ ]] && printf '%s' "$value" || printf '%s' '-1'
}
cleanup() {
  if [[ -r "$PID_FILE" ]]; then
    local pid; pid="$(cat "$PID_FILE" 2>/dev/null || true)"
    [[ "$pid" =~ ^[0-9]+$ ]] && kill "$pid" 2>/dev/null || true
    rm -f "$PID_FILE"
  fi
}
trap cleanup EXIT INT TERM
if command -v mpv >/dev/null 2>&1; then
  args=(--fs --no-terminal --really-quiet --keep-open=no --osd-level=3 --title='OctavianOS')
  [[ -r "$OSD" ]] && args+=(--script="$OSD")
  mpv "${args[@]}" "$VIDEO" >/dev/null 2>&1 &
elif command -v ffplay >/dev/null 2>&1; then
  ffplay -fs -autoexit -loglevel quiet -window_title 'OctavianOS' "$VIDEO" >/dev/null 2>&1 &
else
  echo "OctavianOS splash: mpv/ffplay unavailable; continuing text boot." >&2
  exit 0
fi
player_pid=$!
printf '%s\n' "$player_pid" > "$PID_FILE"
start="$(date +%s)"
while kill -0 "$player_pid" 2>/dev/null; do
  [[ "$(read_percent)" == "100" ]] && break
  now="$(date +%s)"
  (( now - start >= MAX_SECONDS )) && break
  sleep 0.25
done
