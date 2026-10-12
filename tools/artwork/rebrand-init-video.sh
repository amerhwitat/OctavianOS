#!/usr/bin/env bash
# Create a branded splash from the imported Chimera Init.mp4 without mutating source media.
# Requires ffmpeg with drawtext and an installed DejaVu Sans font.
set -Eeuo pipefail
INPUT="${1:-assets/Init.mp4}"
OUTPUT="${2:-build/Init-OctavianOS.mp4}"
FONT="${OCTAVIAN_FONT:-/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf}"
[[ -s "$INPUT" ]] || { echo "missing input video: $INPUT" >&2; exit 2; }
command -v ffmpeg >/dev/null || { echo "ffmpeg is required to rebrand Init.mp4" >&2; exit 2; }
[[ -r "$FONT" ]] || { echo "font file unavailable: $FONT" >&2; exit 2; }
mkdir -p "$(dirname "$OUTPUT")"
# The progress bar is rendered by mpv's live OSD script; it must not be baked into
# the video because boot progress differs by installer, Live CD and installed system.
ffmpeg -hide_banner -y -i "$INPUT" \
  -vf "drawbox=x=0:y=0:w=iw:h=ih*0.23:color=0x04182cbb:t=fill,drawtext=fontfile=$FONT:text='OCTAVIANOS':fontcolor=white:fontsize=h*0.055:x=w*0.055:y=h*0.075:shadowcolor=black@0.8:shadowx=2:shadowy=2,drawtext=fontfile=$FONT:text='OCEANIC COMPUTING':fontcolor=0x8beaf0:fontsize=h*0.022:x=w*0.058:y=h*0.145:shadowcolor=black@0.8:shadowx=2:shadowy=2" \
  -c:v libx264 -preset medium -crf 19 -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart "$OUTPUT"
echo "Branded splash written to $OUTPUT"
