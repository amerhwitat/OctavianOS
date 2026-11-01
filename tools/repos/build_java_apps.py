#!/usr/bin/env python3
"""Compile every Java application in the amerhwitat repos into runnable jars.

For each Java entry point in the repo catalog this script:

  1. Works out the source root (``src/main/java`` when present, else the
     entry point's own directory).
  2. Compiles the tree with ``javac`` into an isolated output directory.
  3. Packages the classes into ``apps/java/dist/<slug>.jar`` with a
     ``Main-Class`` manifest.
  4. Records success / skip / failure in ``desktop/java_apps.json``.

Apps that need JavaFX are skipped unless a JavaFX SDK is on the classpath
(``JAVAFX_LIB``); they are reported rather than silently dropped.

Usage:
    build_java_apps.py --catalog desktop/repo_app_catalog.json \
        --repos /workspace/repos --out apps/java
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

SKIP_PARTS = {"test", "tests"}


def slugify(rel: str) -> str:
    s = rel.replace("/", "-")
    s = re.sub(r"\.java$", "", s)
    return re.sub(r"[^A-Za-z0-9._-]+", "-", s).strip("-").lower()[:90]


def source_root(entry: Path) -> Path:
    parts = entry.parts
    # UI classes sometimes live beside their core package (ui_java / core_java).
    if entry.parent.name in ("ui_java", "gui_java", "ui"):
        core = entry.parent.parent / "core_java"
        if core.is_dir():
            return entry.parent.parent
    if "src" in parts:
        i = parts.index("src")
        if i + 2 < len(parts) and parts[i + 1] in ("main", "test") and parts[i + 2] == "java":
            return Path(*parts[: i + 3])
    return entry.parent


def needs_javafx(files: list[Path]) -> bool:
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "javafx." in text:
            return True
    return False


def build_one(entry: Path, root: Path, outdir: Path, javafx_lib: str | None,
              extra_cp: str | None = None) -> dict:
    sources = [p for p in root.rglob("*.java") if not (set(p.parts) & SKIP_PARTS)]
    if not sources:
        return {"status": "skip", "reason": "no sources"}
    if needs_javafx(sources) and not javafx_lib:
        return {"status": "skip", "reason": "requires JavaFX (no SDK on classpath)"}

    classes = outdir / "classes"
    if classes.exists():
        shutil.rmtree(classes)
    classes.mkdir(parents=True, exist_ok=True)

    cmd = ["javac", "-encoding", "UTF-8", "-nowarn", "-d", str(classes)]
    if extra_cp:
        cmd += ["-cp", extra_cp]
    if javafx_lib:
        cmd += ["--module-path", javafx_lib, "--add-modules", "javafx.controls,javafx.fxml,javafx.web"]
    cmd += [str(s) for s in sources]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return {"status": "fail", "reason": proc.stderr.strip().splitlines()[-1][:300] if proc.stderr else "javac failed"}

    # Determine the main class from the entry point's package declaration.
    text = entry.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^\s*package\s+([\w.]+)\s*;", text, re.M)
    main_class = f"{m.group(1)}.{entry.stem}" if m else entry.stem

    jar = outdir / f"{outdir.name}.jar"
    manifest = outdir / "MANIFEST.MF"
    manifest.write_text(f"Manifest-Version: 1.0\nMain-Class: {main_class}\n\n")
    with zipfile.ZipFile(jar, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(manifest, "META-INF/MANIFEST.MF")
        for cls in classes.rglob("*"):
            if cls.is_file():
                z.write(cls, cls.relative_to(classes).as_posix())
    return {"status": "ok", "jar": str(jar), "main_class": main_class,
            "classes": sum(1 for c in classes.rglob("*.class"))}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--catalog", default="desktop/repo_app_catalog.json")
    ap.add_argument("--repos", default="/workspace/repos")
    ap.add_argument("--out", default="apps/java")
    ap.add_argument("--index", default="desktop/java_apps.json")
    ap.add_argument("--classpath", default=os.environ.get("JAVA_EXTRA_CP"))
    args = ap.parse_args()

    if not shutil.which("javac"):
        print("error: javac not found; install a JDK", file=sys.stderr)
        return 2

    catalog = json.loads(Path(args.catalog).read_text())
    repos_root = Path(args.repos).resolve()
    out = Path(args.out)
    dist = out / "dist"
    work = out / "work"
    dist.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    javafx_lib = os.environ.get("JAVAFX_LIB")

    results = []
    for repo in catalog["repos"]:
        for app in repo["apps"]:
            if app["kind"] != "java":
                continue
            rel = app["rel"]
            if set(Path(rel).parts) & SKIP_PARTS:
                continue
            entry = repos_root / rel
            if not entry.is_file():
                continue
            root = source_root(entry)
            slug = slugify(rel)
            outdir = work / slug
            outdir.mkdir(parents=True, exist_ok=True)
            res = build_one(entry, root, outdir, javafx_lib, args.classpath)
            rec = {"slug": slug, "repo": repo["name"], "source": rel,
                   "main_class": app["main_class"], **res}
            if res["status"] == "ok":
                target = dist / f"{slug}.jar"
                shutil.move(res["jar"], target)
                rec["jar"] = str(target)
            results.append(rec)
            icon = {"ok": "OK  ", "skip": "SKIP", "fail": "FAIL"}[res["status"]]
            print(f"  [{icon}] {slug:52s} {res.get('reason', res.get('main_class', ''))}")

    ok = [r for r in results if r["status"] == "ok"]
    Path(args.index).write_text(json.dumps({
        "schema": "octavianos.java-apps/1",
        "total": len(results),
        "built": len(ok),
        "skipped": sum(1 for r in results if r["status"] == "skip"),
        "failed": sum(1 for r in results if r["status"] == "fail"),
        "apps": results,
    }, indent=2) + "\n")
    print(f"\nbuilt {len(ok)}/{len(results)} jars -> {dist}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
