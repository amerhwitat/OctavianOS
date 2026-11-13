#!/usr/bin/env python3
"""Stage media, apps, documentation, workflows and catalogues into an ISO.

Boot executables remain separately staged and verified. This script adds the
non-boot payload with a manifest and SHA-256 checksums for in-image inspection.
"""
import argparse
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone

MEDIA_EXT = {".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp", ".ico", ".bmp", ".mp4", ".webm", ".mp3", ".wav", ".ogg", ".woff", ".woff2", ".ttf"}
APP_EXT = {".json", ".html", ".js", ".css"}
DOC_EXT = {".md", ".txt", ".pdf"}


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect(root, subdirs, extensions):
    found = []
    for subdir in subdirs:
        base = os.path.join(root, subdir)
        if not os.path.isdir(base):
            continue
        for directory, _dirs, filenames in os.walk(base):
            if any(part in directory for part in ("/build/", "/.git/", "/node_modules/", "/dist/")):
                continue
            for filename in filenames:
                if os.path.splitext(filename)[1].lower() not in extensions:
                    continue
                path = os.path.join(directory, filename)
                if os.path.isfile(path) and not os.path.islink(path):
                    found.append((subdir, path))
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--iso", required=True)
    parser.add_argument("--limit-mb", type=float, default=200.0)
    args = parser.parse_args()

    budget = int(args.limit_mb * 1024 * 1024)
    plan = [
        ("media", ["desktop", "web", "assets", "live-image/artwork", "boot/splash", "boot/visual"], MEDIA_EXT),
        ("apps", ["web", "apps", "desktop"], APP_EXT),
        ("docs", ["docs"], DOC_EXT),
        ("workflows", [".github/workflows"], {".yml", ".yaml"}),
        ("catalogues", ["isa", "tools/commands", "userland/commands", "config", "architecture", "include"], {".json", ".sql", ".h", ".hpp", ".c", ".cpp", ".md"}),
    ]
    destination = os.path.join(args.iso, "payload")
    shutil.rmtree(destination, ignore_errors=True)
    entries, used, skipped = [], 0, 0
    seen = set()
    for kind, subdirs, extensions in plan:
        for _subdir, source in sorted(collect(args.root, subdirs, extensions)):
            relative = os.path.relpath(source, args.root)
            if relative in seen:
                continue
            seen.add(relative)
            size = os.path.getsize(source)
            if used + size > budget:
                skipped += 1
                continue
            target = os.path.join(destination, kind, relative)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copyfile(source, target)
            entries.append({"kind": kind, "path": relative, "bytes": size, "sha256": sha256(source)})
            used += size

    manifest = {
        "schema": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files": len(entries),
        "skipped_over_budget": skipped,
        "bytes": used,
        "kinds": {},
        "entries": entries,
    }
    for entry in entries:
        manifest["kinds"][entry["kind"]] = manifest["kinds"].get(entry["kind"], 0) + 1
    os.makedirs(destination, exist_ok=True)
    with open(os.path.join(destination, "MANIFEST.json"), "w", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=1)
        stream.write("\n")
    with open(os.path.join(destination, "SHA256SUMS"), "w", encoding="utf-8") as stream:
        for entry in entries:
            stream.write(f'{entry["sha256"]}  {entry["kind"]}/{entry["path"]}\n')
    print(f'payload: {len(entries)} files, {used / 1048576:.1f} MiB, kinds={manifest["kinds"]}, skipped={skipped}')


if __name__ == "__main__":
    main()
