#!/usr/bin/env python3
"""Build a machine-readable catalog of every app found in the amerhwitat repos.

Scans a directory of cloned repositories and detects:

  * Python entry points (``if __name__ == "__main__"``), classified as GUI
    (tkinter / PyQt / PySide / GTK) or CLI (argparse / click / plain).
  * Java entry points (``public static void main``).
  * Node.js applications (``package.json`` with a ``scripts`` block).
  * Static HTML surfaces (``index.html`` and friends) that can be served.
  * Maven / Gradle projects.

Output: JSON catalog consumed by ``stage_repo_apps.py`` and by the
OctavianOS Application Center.

Usage:
    build_repo_app_catalog.py --repos /workspace/repos --out desktop/repo_app_catalog.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
    ".mypy_cache", ".pytest_cache", ".idea", ".gradle", "target", ".next",
    "site-packages", "coverage", ".tox",
}

GUI_IMPORTS = (
    "tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6", "gi.repository",
    "wx", "kivy", "customtkinter", "dearpygui",
)
CLI_IMPORTS = ("argparse", "click", "typer", "docopt")

MAIN_RE = re.compile(r"^if\s+__name__\s*==\s*['\"]__main__['\"]", re.M)
JAVA_MAIN_RE = re.compile(r"public\s+static\s+void\s+main\s*\(")
TITLE_RE = re.compile(r"""title\s*[=:]\s*[fF]?['"]([^'"\n]{3,80})['"]""")


def walk(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".git")]
        for name in filenames:
            yield Path(dirpath) / name


def read_text(path: Path, limit: int = 200_000) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            return fh.read(limit)
    except OSError:
        return ""


def classify_python(path: Path, text: str) -> dict[str, Any] | None:
    if not MAIN_RE.search(text):
        return None
    gui = any(f"import {m}" in text or f"from {m}" in text for m in GUI_IMPORTS)
    cli = any(f"import {m}" in text or f"from {m}" in text for m in CLI_IMPORTS)
    title = None
    m = TITLE_RE.search(text)
    if m:
        title = m.group(1).strip()
    return {
        "kind": "python-gui" if gui else "python-cli",
        "language": "python",
        "entry": str(path),
        "has_gui": gui,
        "uses_cli_framework": cli,
        "title": title,
        "needs_gui_wrapper": not gui,
    }


def classify_java(path: Path, text: str) -> dict[str, Any] | None:
    if not JAVA_MAIN_RE.search(text):
        return None
    pkg = None
    m = re.search(r"^\s*package\s+([\w.]+)\s*;", text, re.M)
    if m:
        pkg = m.group(1)
    cls = path.stem
    fqcn = f"{pkg}.{cls}" if pkg else cls
    return {
        "kind": "java",
        "language": "java",
        "entry": str(path),
        "main_class": fqcn,
        "has_gui": ("javafx" in text.lower() or "swing" in text.lower()
                    or "extends Application" in text),
    }


def classify_node(pkg_path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(read_text(pkg_path))
    except (json.JSONDecodeError, OSError):
        return None
    scripts = data.get("scripts") or {}
    if not scripts:
        return None
    start = scripts.get("start") or scripts.get("dev") or next(iter(scripts.values()))
    return {
        "kind": "node",
        "language": "javascript",
        "entry": str(pkg_path.parent),
        "name": data.get("name") or pkg_path.parent.name,
        "version": data.get("version"),
        "scripts": sorted(scripts),
        "start_script": start,
        "has_gui": "web" in str(pkg_path).lower() or "threejs" in str(pkg_path).lower(),
    }


def classify_html(path: Path) -> dict[str, Any]:
    text = read_text(path, 40_000)
    title = None
    m = re.search(r"<title[^>]*>([^<]{2,80})</title>", text, re.I)
    if m:
        title = m.group(1).strip()
    return {
        "kind": "web",
        "language": "html",
        "entry": str(path),
        "title": title,
        "has_gui": True,
    }


def build(repos_root: Path) -> dict[str, Any]:
    repos: list[dict[str, Any]] = []
    totals = {"python-gui": 0, "python-cli": 0, "java": 0, "node": 0, "web": 0}

    for repo_dir in sorted(p for p in repos_root.iterdir() if p.is_dir()):
        apps: list[dict[str, Any]] = []
        maven, gradle = [], []

        for path in walk(repo_dir):
            name = path.name
            suffix = path.suffix.lower()
            rel = str(path.relative_to(repos_root))

            if suffix == ".py":
                text = read_text(path)
                app = classify_python(path, text)
                if app:
                    app["id"] = rel.replace("/", ".")[:-3]
                    app["repo"] = repo_dir.name
                    app["rel"] = rel
                    apps.append(app)
                    totals[app["kind"]] += 1
            elif suffix == ".java":
                text = read_text(path)
                app = classify_java(path, text)
                if app:
                    app["id"] = rel.replace("/", ".")[:-5]
                    app["repo"] = repo_dir.name
                    app["rel"] = rel
                    apps.append(app)
                    totals["java"] += 1
            elif name == "package.json":
                app = classify_node(path)
                if app:
                    app["id"] = rel.replace("/", ".")
                    app["repo"] = repo_dir.name
                    app["rel"] = rel
                    apps.append(app)
                    totals["node"] += 1
            elif name in ("index.html", "main.html", "app.html"):
                app = classify_html(path)
                app["id"] = rel.replace("/", ".")
                app["repo"] = repo_dir.name
                app["rel"] = rel
                apps.append(app)
                totals["web"] += 1
            elif name == "pom.xml":
                maven.append(rel)
            elif name in ("build.gradle", "build.gradle.kts"):
                gradle.append(rel)

        repos.append({
            "name": repo_dir.name,
            "apps": apps,
            "maven_projects": maven,
            "gradle_projects": gradle,
            "counts": {
                "python-gui": sum(1 for a in apps if a["kind"] == "python-gui"),
                "python-cli": sum(1 for a in apps if a["kind"] == "python-cli"),
                "java": sum(1 for a in apps if a["kind"] == "java"),
                "node": sum(1 for a in apps if a["kind"] == "node"),
                "web": sum(1 for a in apps if a["kind"] == "web"),
            },
        })

    return {
        "schema": "octavianos.repo-app-catalog/1",
        "repos_root": str(repos_root),
        "repo_count": len(repos),
        "totals": totals,
        "app_count": sum(len(r["apps"]) for r in repos),
        "needs_gui_wrapper": sorted(
            a["rel"] for r in repos for a in r["apps"]
            if a.get("needs_gui_wrapper")
        ),
        "repos": repos,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repos", default="/workspace/repos")
    ap.add_argument("--out", default="desktop/repo_app_catalog.json")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    root = Path(args.repos).resolve()
    if not root.is_dir():
        print(f"error: repos root not found: {root}", file=sys.stderr)
        return 2

    catalog = build(root)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")

    if not args.quiet:
        print(f"repos:  {catalog['repo_count']}")
        print(f"apps:   {catalog['app_count']}")
        for k, v in catalog["totals"].items():
            print(f"  {k:12s} {v}")
        print(f"need GUI wrapper: {len(catalog['needs_gui_wrapper'])}")
        print(f"written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
