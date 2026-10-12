#!/usr/bin/env python3
"""Compare a vendored source snapshot with a separately checked-out upstream tree.

The report is an inventory comparison only: it does not compare Git history,
prove semantic parity, or establish that any target builds or boots.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

IGNORED_DIRS = {".git", "__pycache__", ".pytest_cache"}


def inventory(root: Path) -> set[str]:
    files: set[str] = set()
    for path in root.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.is_file():
            files.add(path.relative_to(root).as_posix())
    return files


def compare(upstream: Path, vendored: Path) -> dict[str, object]:
    upstream_files = inventory(upstream)
    vendored_files = inventory(vendored)
    return {
        "upstream_root": str(upstream),
        "vendored_root": str(vendored),
        "upstream_file_count": len(upstream_files),
        "vendored_file_count": len(vendored_files),
        "missing_from_vendor": sorted(upstream_files - vendored_files),
        "extra_in_vendor": sorted(vendored_files - upstream_files),
        "inventory_only": True,
        "history_compared": False,
        "build_or_boot_verified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", required=True, type=Path)
    parser.add_argument("--vendored", required=True, type=Path)
    parser.add_argument("--output", type=Path, help="Write JSON report to this path")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero if inventories differ")
    args = parser.parse_args()

    for label, root in (("upstream", args.upstream), ("vendored", args.vendored)):
        if not root.is_dir():
            parser.error(f"{label} directory does not exist: {root}")

    report = compare(args.upstream.resolve(), args.vendored.resolve())
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    differs = bool(report["missing_from_vendor"] or report["extra_in_vendor"])
    return 1 if args.strict and differs else 0


if __name__ == "__main__":
    raise SystemExit(main())
