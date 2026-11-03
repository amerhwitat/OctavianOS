#!/usr/bin/env bash
set -euo pipefail

# Launch only a locally installed VoiceConnect package. Otherwise open the
# upstream project page; this fallback never reports the application installed.
candidates=(
  "${OCTAVIAN_VOICECONNECT_BIN:-}"
  /opt/voiceconnect/VoiceConnect
  /opt/voiceconnect/voiceconnect
  /usr/local/bin/voiceconnect
  /usr/bin/voiceconnect
)
for candidate in "${candidates[@]}"; do
  [[ -n "$candidate" && -x "$candidate" ]] || continue
  exec "$candidate" "$@"
done

url="https://github.com/amerhwitat/test/tree/feat/voiceconnect-p2p-camera"
if command -v xdg-open >/dev/null 2>&1; then
  exec xdg-open "$url"
fi
printf '[OctavianOS] VoiceConnect is not installed. Review the upstream package at %s\n' "$url" >&2
exit 127
