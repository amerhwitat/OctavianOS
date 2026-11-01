#!/usr/bin/env python3
"""Compare file paths and SHA-256 content for a vendored source snapshot."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

IGNORED_DIRS = {".git", "__pycache__", ".pytest_cache"}


def inventory(root: Path) -> dict[str, str]:
    """Return relative POSIX paths mapped to SHA-256 digests of file bytes."""
    files: dict[str, str] = {}
    for path in root.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.is_file():
            files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return files


def compare(upstream: Path, vendored: Path, upstream_revision: str | None = None) -> dict[str, object]:
    upstream_files = inventory(upstream)
    vendored_files = inventory(vendored)
    upstream_paths = set(upstream_files)
    vendored_paths = set(vendored_files)
    common = upstream_paths & vendored_paths
    different_content = [
        {
            "path": path,
            "upstream_sha256": upstream_files[path],
            "vendored_sha256": vendored_files[path],
        }
        for path in sorted(common)
        if upstream_files[path] != vendored_files[path]
    ]
    return {
        "upstream_root": str(upstream),
        "vendored_root": str(vendored),
        "upstream_revision": upstream_revision,
        "upstream_file_count": len(upstream_paths),
        "vendored_file_count": len(vendored_paths),
        "missing_from_vendor": sorted(upstream_paths - vendored_paths),
        "extra_in_vendor": sorted(vendored_paths - upstream_paths),
        "different_content": different_content,
        "path_and_content_hashes_compared": True,
        "history_compared": False,
        "build_or_boot_verified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", required=True, type=Path)
    parser.add_argument("--vendored", required=True, type=Path)
    parser.add_argument("--upstream-revision", help="Git revision of the upstream checkout")
    parser.add_argument("--output", type=Path, help="Write JSON report to this path")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero if paths or contents differ")
    args = parser.parse_args()

    for label, root in (("upstream", args.upstream), ("vendored", args.vendored)):
        if not root.is_dir():
            parser.error(f"{label} directory does not exist: {root}")

    report = compare(args.upstream.resolve(), args.vendored.resolve(), args.upstream_revision)
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    differs = bool(
        report["missing_from_vendor"]
        or report["extra_in_vendor"]
        or report["different_content"]
    )
    return 1 if args.strict and differs else 0


if __name__ == "__main__":
    raise SystemExit(main())
