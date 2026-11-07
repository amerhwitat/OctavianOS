#!/usr/bin/env python3
"""Export and verify every app-* symbol in Aurora's original 133-icon sprite."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

SVG_NS = "{http://www.w3.org/2000/svg}"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sprite", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    for path in (args.sprite, args.manifest):
        if not path.is_file() or path.stat().st_size == 0:
            raise SystemExit(f"required Aurora app-icon input is missing or empty: {path}")

    source_manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if source_manifest.get("schema") != "chimera-octavian-app-icons/v1":
        raise SystemExit("unsupported Aurora app-icon manifest schema")
    apps = source_manifest.get("apps")
    if not isinstance(apps, list) or not apps:
        raise SystemExit("app-icon manifest has no app records")
    expected = [item.get("id") for item in apps]
    if not all(isinstance(name, str) and re.fullmatch(r"[a-z0-9][a-z0-9._-]*", name)
               for name in expected):
        raise SystemExit("app-icon manifest contains an invalid id")
    if len(expected) != len(set(expected)):
        raise SystemExit("app-icon manifest contains duplicate ids")
    if source_manifest.get("count") != len(expected):
        raise SystemExit("app-icon manifest count does not match its app records")

    root = ET.parse(args.sprite).getroot()
    symbols = [node for node in root.iter(SVG_NS + "symbol")
               if node.get("id", "").startswith("app-")]
    actual = [node.get("id", "")[4:] for node in symbols]
    if len(actual) != len(set(actual)):
        raise SystemExit("Aurora sprite contains duplicate app-* symbols")
    if set(actual) != set(expected):
        raise SystemExit(
            f"sprite/manifest mismatch: missing={sorted(set(expected)-set(actual))}, "
            f"unexpected={sorted(set(actual)-set(expected))}"
        )

    defs = root.find(SVG_NS + "defs")
    gradients = list(defs) if defs is not None else []
    args.output.mkdir(parents=True, exist_ok=True)
    entries = []
    for symbol in symbols:
        icon_id = symbol.get("id", "")[4:]
        svg = ET.Element(SVG_NS + "svg", {
            "viewBox": symbol.get("viewBox", "0 0 64 64"),
            "role": "img",
            "aria-label": icon_id,
        })
        svg_defs = ET.SubElement(svg, SVG_NS + "defs")
        for gradient in gradients:
            svg_defs.append(ET.fromstring(ET.tostring(gradient, encoding="unicode")))
        for child in list(symbol):
            svg.append(ET.fromstring(ET.tostring(child, encoding="unicode")))
        target = args.output / f"chimera-{icon_id}.svg"
        ET.ElementTree(svg).write(target, encoding="utf-8", xml_declaration=True)
        ET.parse(target)
        entries.append({"id": icon_id, "file": target.name,
                        "symbol": "#app-" + icon_id, "sha256": digest(target)})

    output_manifest = {
        "schema": "chimera-aurora-hicolor-icons/v1",
        "count": len(entries),
        "source_sprite_sha256": digest(args.sprite),
        "source_manifest_sha256": digest(args.manifest),
        "icons": entries,
    }
    (args.output / "manifest.json").write_text(
        json.dumps(output_manifest, indent=2) + "\n", encoding="utf-8"
    )
    if len(entries) != source_manifest["count"]:
        raise SystemExit("not every catalogued Aurora app icon was exported")
    print(f"Exported and verified all {len(entries)} catalogued Aurora app icons")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
