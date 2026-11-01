#!/usr/bin/env python3
"""Render OctavianOS source artwork into a firmware-friendly PNG.

This generates an artifact for an ISO builder; it does not claim that any ISO
contains the resulting image. GRUB/firmware boot stages should use the PNG,
while the desktop may continue using the original SVG.
"""
from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT / "desktop/aurora/assets/octavian-octopus-aurora.svg"


def render(source: Path, output: Path, width: int, height: int) -> dict[str, int | str]:
    if width < 640 or height < 360:
        raise ValueError("boot artwork output must be at least 640x360")
    if not source.is_file() or source.stat().st_size < 100:
        raise ValueError(f"missing or empty SVG source: {source}")
    try:
        import cairosvg
    except ImportError as exc:
        raise RuntimeError("CairoSVG is required; install python3-cairosvg or pip install CairoSVG") from exc

    output.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2png(url=str(source), write_to=str(output),
                     output_width=width, output_height=height)
    data = output.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError(f"renderer did not produce a valid PNG: {output}")
    actual_width, actual_height = struct.unpack(">II", data[16:24])
    if (actual_width, actual_height) != (width, height):
        raise RuntimeError(
            f"PNG dimensions mismatch: expected {width}x{height}, got {actual_width}x{actual_height}"
        )
    return {"source": str(source), "output": str(output), "width": actual_width,
            "height": actual_height, "bytes": len(data)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    args = parser.parse_args()
    try:
        report = render(args.source, args.output, args.width, args.height)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"boot artwork render failed: {exc}", file=sys.stderr)
        return 2
    print("boot artwork render passed: " + " ".join(f"{key}={value}" for key, value in report.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
