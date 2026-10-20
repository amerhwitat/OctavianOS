#!/usr/bin/env python3
"""Stage all offline OctavianOS/Chimera desktop art, media, menus and icons."""
import argparse, hashlib, json, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
CHIMERA = ROOT / "vendor/chimera-ii-os/source"
EXT = {".svg", ".png", ".jpg", ".jpeg", ".webp", ".mp4", ".wav", ".ogg", ".ttf", ".otf"}

def collect(base):
    out = set()
    for rel in ("desktop/aurora/assets", "desktop/marine/assets", "desktop/artwork",
                "desktop/sessions", "desktop/aurora", "desktop/marine", "apps", "boot/splash"):
        folder = base / rel
        if not folder.is_dir(): continue
        for p in folder.rglob("*"):
            if not p.is_file(): continue
            if p.suffix.lower() in EXT or (p.suffix.lower() == ".json" and
                any(k in p.name.lower() for k in ("manifest","catalog","menu","session","wallpaper","icon","artwork"))):
                out.add(p)
    return sorted(out)

def stage(bases, destination):
    rows, found = [], set()
    for base in bases:
        for src in collect(base):
            if not src.stat().st_size: continue
            dst = destination / base.name / src.relative_to(base)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            found.add(src.name)
            rows.append({"path":str(dst.relative_to(destination)),"size":dst.stat().st_size,
                         "sha256":hashlib.sha256(dst.read_bytes()).hexdigest()})
    missing = {"octavian-octopus-aurora.svg","marine-desktop.svg","Init.mp4"} - found
    if missing: raise RuntimeError("required artifacts missing: " + ", ".join(sorted(missing)))
    destination.mkdir(parents=True, exist_ok=True)
    report = {"schema":"OCTAVIAN-DESKTOP-STAGE-1","status":"staged-not-boot-verified","file_count":len(rows),"files":rows}
    (destination / "desktop-artifact-inventory.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rootfs",type=Path,default=CHIMERA/"rootfs")
    ap.add_argument("--initramfs-root",type=Path,default=CHIMERA/"build/live-boot/initramfs/root")
    ap.add_argument("--iso-root",type=Path)
    a=ap.parse_args()
    bases=(ROOT,CHIMERA)
    dests=[a.rootfs/"usr/share/octavian/desktop-assets",a.initramfs_root/"usr/share/octavian/desktop-assets"]
    if a.iso_root: dests.append(a.iso_root/"boot/visual/octavian-desktop-assets")
    report=None
    for dest in dests: report=stage(bases,dest)
    print(f"[OCTAVIAN-DESKTOP-ASSETS] staged {report['file_count']} files; status=staged-not-boot-verified")
    return 0

if __name__=="__main__":
    try: raise SystemExit(main())
    except (OSError,RuntimeError) as exc: raise SystemExit(f"[OCTAVIAN-DESKTOP-ASSETS][ERROR] {exc}")
