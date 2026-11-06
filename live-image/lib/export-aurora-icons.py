#!/usr/bin/env python3
"""Export real embedded Aurora SVG icons into a freedesktop icon theme."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.source.is_file():
        raise SystemExit(f"missing compiled Aurora icon source: {args.source}")
    source = args.source.read_text(encoding="utf-8")
    pattern = re.compile(r'\{"([^"]+)","(<svg[\s\S]*?</svg>)"\}')
    icons = pattern.findall(source)
    if not icons:
        raise SystemExit("no embedded SVG icons found; refusing to emit an empty icon theme")
    apps = args.output / "scalable" / "apps"
    apps.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name, svg in icons:
        if not re.fullmatch(r"[A-Za-z0-9_.+-]+", name):
            raise SystemExit(f"unsafe icon identifier: {name!r}")
        target = apps / f"chimera-{name}.svg"
        target.write_text(svg + "\n", encoding="utf-8")
        manifest.append({"name": name, "file": f"scalable/apps/{target.name}",
                         "source": str(args.source)})
    (args.output / "index.theme").write_text(
        "[Icon Theme]\nName=Chimera Aurora\nComment=Generated from the embedded Aurora SVG catalogue\n"
        "Directories=scalable/apps\nInherits=Adwaita,hicolor\n\n[scalable/apps]\nSize=48\nType=Scalable\nMinSize=16\nMaxSize=256\n",
        encoding="utf-8")
    (args.output / "manifest.json").write_text(json.dumps({
        "schema": "CHIMERA-AURORA-ICON-EXPORT-1",
        "source_sha256": __import__("hashlib").sha256(args.source.read_bytes()).hexdigest(),
        "count": len(manifest), "icons": manifest
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(manifest)} genuine SVG icons to {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
