#!/usr/bin/env python3
"""Export the complete, catalogued Aurora SVG icon set into a freedesktop theme."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True,
                        help="icon_theme.json declaring the complete expected icon set")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    for path in (args.source, args.catalog):
        if not path.is_file():
            raise SystemExit(f"required Aurora icon input is missing: {path}")

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    if catalog.get("schema") != "CHM-AURORA-ICON-1":
        raise SystemExit("unsupported Aurora icon catalogue schema")
    expected = catalog.get("icons")
    if not isinstance(expected, list) or not expected or not all(
        isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9_.+-]+", name)
        for name in expected
    ):
        raise SystemExit("Aurora icon catalogue is empty or contains invalid identifiers")
    if len(expected) != len(set(expected)):
        raise SystemExit("Aurora icon catalogue contains duplicate identifiers")

    source = args.source.read_text(encoding="utf-8")
    pattern = re.compile(r'\{"([^"]+)","(<svg[\s\S]*?</svg>)"\}')
    matches = pattern.findall(source)
    names = [name for name, _ in matches]
    if not matches:
        raise SystemExit("no embedded SVG icons found; refusing to emit an empty icon theme")
    if len(names) != len(set(names)):
        raise SystemExit("embedded Aurora source contains duplicate icon identifiers")
    if set(names) != set(expected):
        missing = sorted(set(expected) - set(names))
        unexpected = sorted(set(names) - set(expected))
        raise SystemExit(f"icon catalogue/source mismatch; missing={missing}, unexpected={unexpected}")

    apps = args.output / "scalable" / "apps"
    apps.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name, svg in matches:
        try:
            root = ET.fromstring(svg)
        except ET.ParseError as exc:
            raise SystemExit(f"invalid SVG for {name}: {exc}") from exc
        if root.tag.rsplit("}", 1)[-1] != "svg":
            raise SystemExit(f"icon {name} does not have an SVG root element")
        target = apps / f"chimera-{name}.svg"
        target.write_text(svg + "\n", encoding="utf-8")
        manifest.append({
            "name": name,
            "file": f"scalable/apps/{target.name}",
            "sha256": sha256(target),
        })

    (args.output / "index.theme").write_text(
        "[Icon Theme]\nName=Chimera Aurora\n"
        "Comment=Generated from the complete embedded Aurora SVG catalogue\n"
        "Directories=scalable/apps\nInherits=Adwaita,hicolor\n\n"
        "[scalable/apps]\nSize=48\nType=Scalable\nMinSize=16\nMaxSize=256\n",
        encoding="utf-8",
    )
    (args.output / "manifest.json").write_text(json.dumps({
        "schema": "CHIMERA-AURORA-ICON-EXPORT-1",
        "source_sha256": sha256(args.source),
        "catalog_sha256": sha256(args.catalog),
        "count": len(manifest),
        "icons": manifest,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Exported and validated all {len(manifest)} catalogued Aurora SVG icons")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
