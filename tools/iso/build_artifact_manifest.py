#!/usr/bin/env python3
"""Create a deterministic SHA-256 inventory for an ISO staging tree."""
import argparse
import hashlib
import json
import os
import stat
import sys
from pathlib import Path

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def kind(name):
    ext=Path(name).suffix.lower()
    if ext in {".img",".initrd",".initramfs"}: return "ram-disk-image"
    if ext in {".iso",".zst"}: return "disk-or-optical-image"
    if ext in {".elf",".efi"}: return "executable-image"
    if ext in {".bin",".o",".obj"}: return "boot-binary"
    if ext in {".squashfs",".sqfs"}: return "root-filesystem-image"
    if ext in {".mp4",".png",".jpg",".jpeg",".svg",".webp"}: return "visual-media"
    if ext in {".json",".toml",".yaml",".yml"}: return "metadata"
    return "file"

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",required=True,type=Path)
    p.add_argument("--manifest",required=True,type=Path)
    p.add_argument("--checksums",type=Path)
    p.add_argument("--require",action="append",default=[])
    a=p.parse_args()
    root=a.root.resolve()
    if not root.is_dir(): p.error(f"not an ISO staging directory: {root}")
    missing=[x for x in a.require if not (root/x).is_file() or (root/x).is_symlink()]
    if missing:
        print("ERROR: required ISO artifacts missing: "+", ".join(missing),file=sys.stderr)
        return 2
    manifest=a.manifest.resolve()
    checksums=a.checksums.resolve() if a.checksums else None
    excluded={manifest,checksums}
    records=[]
    for path in sorted(root.rglob("*"),key=lambda x:x.relative_to(root).as_posix()):
        if not path.is_file() and not path.is_symlink(): continue
        if path.resolve(strict=False) in excluded: continue
        rel=path.relative_to(root).as_posix()
        if path.is_symlink():
            target=os.readlink(path); raw=target.encode("utf-8",errors="surrogateescape")
            records.append({"path":rel,"kind":"symlink","bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"target":target})
        else:
            st=path.stat()
            records.append({"path":rel,"kind":kind(rel),"bytes":st.st_size,"sha256":sha256(path),"mode":stat.S_IMODE(st.st_mode)})
    if not records:
        print("ERROR: ISO staging tree is empty",file=sys.stderr); return 2
    counts={}
    for r in records: counts[r["kind"]]=counts.get(r["kind"],0)+1
    doc={"schema":"OCTAVIAN-ISO-ARTIFACTS-1","artifact_count":len(records),
         "kind_counts":dict(sorted(counts.items())),"required_artifacts":a.require,"artifacts":records}
    manifest.parent.mkdir(parents=True,exist_ok=True)
    manifest.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    if checksums:
        checksums.parent.mkdir(parents=True,exist_ok=True)
        checksums.write_text("\n".join(f'{r["sha256"]}  {r["path"]}' for r in records if r["kind"]!="symlink")+"\n",encoding="utf-8")
    print(f"[ISO ARTIFACTS] inventoried={len(records)} kinds={json.dumps(dict(sorted(counts.items())),sort_keys=True)}")
    return 0

if __name__=="__main__": raise SystemExit(main())
