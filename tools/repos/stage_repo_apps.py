#!/usr/bin/env python3
"""Stage every amerhwitat repo app into an OctavianOS rootfs.

Copies each repository (minus VCS/build noise) to
``<rootfs>/opt/octavianos/repos/<repo>`` and generates:

  * ``repos/index.html``  — the Repo App Explorer, a searchable web UI that
    links every Python, Java, Node and HTML app found in the catalog.
  * ``repos/repo-apps.json`` — machine-readable manifest for the desktops.
  * ``repos/README.txt`` — how to run each app class inside the image.

Usage:
    stage_repo_apps.py --repos /workspace/repos \
        --catalog desktop/repo_app_catalog.json \
        --rootfs build/iso/rootfs
"""

from __future__ import annotations

import argparse
import html
import json
import os
import shutil
from pathlib import Path

EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
    ".mypy_cache", ".pytest_cache", ".idea", ".gradle", "target", ".next",
    "coverage", ".tox", ".git-lfs",
}
EXCLUDE_SUFFIX = {".iso", ".img", ".qcow2", ".vmdk", ".pyc", ".pyo", ".class", ".jar"}
MAX_FILE_BYTES = 24 * 1024 * 1024


def copy_repo(src: Path, dst: Path) -> tuple[int, int]:
    files = 0
    total = 0
    for dirpath, dirnames, filenames in os.walk(src):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        rel = Path(dirpath).relative_to(src)
        (dst / rel).mkdir(parents=True, exist_ok=True)
        for name in filenames:
            sp = Path(dirpath) / name
            if sp.suffix.lower() in EXCLUDE_SUFFIX:
                continue
            try:
                size = sp.stat().st_size
            except OSError:
                continue
            if size > MAX_FILE_BYTES:
                continue
            try:
                shutil.copy2(sp, dst / rel / name)
                files += 1
                total += size
            except OSError:
                pass
    return files, total


def build_index(catalog: dict, staged: dict[str, str]) -> str:
    rows = []
    for repo in catalog["repos"]:
        name = repo["name"]
        for app in repo["apps"]:
            kind = app["kind"]
            rel = app["rel"]
            title = app.get("title") or Path(rel).stem.replace("_", " ").title()
            if kind == "web":
                href = f"{name}/{rel}"
                action = f'<a class="open" href="{html.escape(href)}">Open UI</a>'
            elif kind == "python-gui":
                action = '<span class="tag py">GUI</span>'
            elif kind == "python-cli":
                action = '<span class="tag wrap">GUI wrapper</span>'
            elif kind == "java":
                action = '<span class="tag java">Java</span>'
            else:
                action = '<span class="tag node">Node</span>'
            rows.append(
                f'<tr data-k="{kind}" data-r="{html.escape(name)}" '
                f'data-s="{html.escape((name + " " + rel + " " + title).lower())}">'
                f'<td>{html.escape(name)}</td><td>{html.escape(title)}</td>'
                f'<td><code>{html.escape(rel)}</code></td><td>{action}</td></tr>'
            )

    counts = catalog["totals"]
    chips = "".join(
        f'<button class="chip" data-f="{k}">{k} <b>{v}</b></button>'
        for k, v in counts.items()
    )
    repo_opts = "".join(
        f'<option value="{html.escape(r["name"])}">{html.escape(r["name"])} ({len(r["apps"])})</option>'
        for r in catalog["repos"]
    )

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>OctavianOS — Repo App Explorer</title>
<style>
:root{{--bg:#080c14;--panel:#111a2b;--line:#1e2b44;--fg:#e8eefc;--dim:#8a9ab8;--accent:#4da3ff;--ok:#39d98a;--java:#f0a24b;--node:#7ee787;--py:#4da3ff}}
*{{box-sizing:border-box}}
body{{margin:0;font:14px/1.5 "DejaVu Sans",system-ui,sans-serif;background:radial-gradient(1200px 600px at 20% -10%,#16233a,#080c14 60%);color:var(--fg);min-height:100vh}}
header{{padding:26px 32px 18px;border-bottom:1px solid var(--line);background:rgba(9,14,24,.7);backdrop-filter:blur(14px);position:sticky;top:0;z-index:5}}
h1{{margin:0 0 4px;font-size:22px;letter-spacing:.2px}}
h1 span{{color:var(--accent)}}
.sub{{color:var(--dim);font-size:12.5px}}
.toolbar{{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px;align-items:center}}
input[type=search],select{{background:var(--panel);border:1px solid var(--line);color:var(--fg);padding:9px 12px;border-radius:9px;font:inherit;outline:none}}
input[type=search]{{flex:1;min-width:220px}}
input[type=search]:focus,select:focus{{border-color:var(--accent)}}
.chip{{background:var(--panel);border:1px solid var(--line);color:var(--dim);padding:7px 12px;border-radius:999px;cursor:pointer;font:inherit;font-size:12px}}
.chip b{{color:var(--fg)}}
.chip.on{{border-color:var(--accent);color:var(--fg);background:#12233c}}
main{{padding:18px 32px 60px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{text-align:left;color:var(--dim);font-weight:600;font-size:11.5px;text-transform:uppercase;letter-spacing:.08em;padding:8px 10px;border-bottom:1px solid var(--line);position:sticky;top:126px;background:#0a101b}}
td{{padding:9px 10px;border-bottom:1px solid rgba(30,43,68,.55);vertical-align:top}}
tr:hover td{{background:rgba(77,163,255,.06)}}
code{{font-family:"DejaVu Sans Mono",monospace;font-size:12px;color:#a9c4e8}}
.tag{{font-size:10.5px;padding:2px 7px;border-radius:6px;border:1px solid var(--line);color:var(--dim)}}
.tag.py{{color:var(--py);border-color:#1d3f66}}
.tag.java{{color:var(--java);border-color:#5a3d1c}}
.tag.node{{color:var(--node);border-color:#1f4d2b}}
.tag.wrap{{color:#c9a6ff;border-color:#3d2a5c}}
a.open{{color:var(--accent);text-decoration:none;font-weight:600}}
a.open:hover{{text-decoration:underline}}
.empty{{padding:40px;text-align:center;color:var(--dim)}}
footer{{padding:16px 32px;color:var(--dim);font-size:11.5px;border-top:1px solid var(--line)}}
</style></head><body>
<header>
  <h1>OctavianOS <span>Repo App Explorer</span></h1>
  <div class="sub">{catalog['repo_count']} repositories · {catalog['app_count']} applications · Python · Java · Node.js · Web</div>
  <div class="toolbar">
    <input id="q" type="search" placeholder="Search apps, paths, repositories…" autocomplete="off">
    <select id="repo"><option value="">All repositories</option>{repo_opts}</select>
    {chips}
  </div>
</header>
<main>
<table><thead><tr><th>Repo</th><th>App</th><th>Path</th><th>Kind</th></tr></thead>
<tbody id="rows">{''.join(rows)}</tbody></table>
<div id="empty" class="empty" hidden>No apps match the current filter.</div>
</main>
<footer>OctavianOS · every app from github.com/amerhwitat, staged at /opt/octavianos/repos</footer>
<script>
const q=document.getElementById('q'),repo=document.getElementById('repo'),
      rows=[...document.querySelectorAll('#rows tr')],empty=document.getElementById('empty');
let kind='';
function apply(){{
  const term=q.value.trim().toLowerCase(),r=repo.value;let n=0;
  for(const row of rows){{
    const ok=(!term||row.dataset.s.includes(term))&&(!r||row.dataset.r===r)&&(!kind||row.dataset.k===kind);
    row.hidden=!ok;if(ok)n++;
  }}
  empty.hidden=n>0;
}}
q.addEventListener('input',apply);repo.addEventListener('change',apply);
document.querySelectorAll('.chip').forEach(c=>c.addEventListener('click',()=>{{
  const f=c.dataset.f;kind=(kind===f)?'':f;
  document.querySelectorAll('.chip').forEach(x=>x.classList.toggle('on',x===c&&kind));
  apply();
}}));
</script></body></html>
"""


README = """OctavianOS — repository applications
=====================================

Everything from github.com/amerhwitat is staged here.

Layout
------
  <repo>/...                original sources (VCS/build noise removed)
  index.html                searchable Repo App Explorer (open in a browser)
  repo-apps.json            machine-readable app manifest

Running the apps
----------------
Python GUI apps        :  python3 <repo>/<path>.py
Python CLI apps        :  python3 /opt/octavianos/apps/repo-gui/generated/<slug>.py
                          (opens a Tk window with arguments + live output)
Python GUI wrappers    :  /opt/octavianos/apps/repo-gui/generated/*.desktop
Java apps              :  java -cp /opt/octavianos/repos/java-classes <main-class>
Node.js apps           :  cd <repo>/<dir> && npm install && npm start
Web UIs                :  open index.html, or http://127.0.0.1:8080/repos/<repo>/<path>

PyInstaller binaries
--------------------
Standalone one-file executables built from the Python apps live in
/opt/octavianos/apps/bin/.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repos", default="/workspace/repos")
    ap.add_argument("--catalog", default="desktop/repo_app_catalog.json")
    ap.add_argument("--rootfs", required=True)
    ap.add_argument("--dest", default="/opt/octavianos/repos")
    args = ap.parse_args()

    repos_root = Path(args.repos).resolve()
    catalog = json.loads(Path(args.catalog).read_text())
    dest = Path(args.rootfs) / args.dest.lstrip("/")
    dest.mkdir(parents=True, exist_ok=True)

    staged: dict[str, str] = {}
    total_files = total_bytes = 0
    for repo in catalog["repos"]:
        src = repos_root / repo["name"]
        if not src.is_dir():
            continue
        files, size = copy_repo(src, dest / repo["name"])
        staged[repo["name"]] = f"{files} files, {size / 1e6:.1f} MB"
        total_files += files
        total_bytes += size
        print(f"  staged {repo['name']:24s} {files:5d} files  {size / 1e6:7.1f} MB")

    (dest / "index.html").write_text(build_index(catalog, staged))
    (dest / "README.txt").write_text(README)
    (dest / "repo-apps.json").write_text(json.dumps({
        "schema": "octavianos.repo-apps/1",
        "catalog": catalog,
        "staged": staged,
        "totals": {"files": total_files, "bytes": total_bytes},
    }, indent=2) + "\n")

    print(f"total: {total_files} files, {total_bytes / 1e6:.1f} MB -> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
