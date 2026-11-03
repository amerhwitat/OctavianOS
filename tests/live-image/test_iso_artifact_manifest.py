import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[2]/"tools"/"iso"/"build_artifact_manifest.py"

class IsoArtifactManifestTests(unittest.TestCase):
    def test_required_boot_payload_is_hash_inventoried(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"iso"
            payload={
                "live/vmlinuz":b"kernel",
                "live/initrd.img":b"initrd",
                "live/filesystem.squashfs":b"rootfs",
                "boot/grub/grub.cfg":b"menu",
                "boot/koronos.elf":b"ELF",
                "boot/spitfire/stage2.bin":b"SF2",
                "boot/candidates/installer/installation.img":b"installer",
                "boot/candidates/recovery/chimera-recovery-initramfs.img":b"recovery",
                "boot/candidates/native-runtime-candidates.json":b"{}",
            }
            for rel,data in payload.items():
                p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            manifest=root/"boot/artifact-manifest.json"
            sums=root/"boot/SHA256SUMS"
            args=[sys.executable,str(SCRIPT),"--root",str(root),"--manifest",str(manifest),"--checksums",str(sums)]
            for rel in payload: args += ["--require",rel]
            subprocess.run(args,check=True,capture_output=True,text=True)
            doc=json.loads(manifest.read_text())
            rows={x["path"]:x for x in doc["artifacts"]}
            self.assertEqual(doc["schema"],"OCTAVIAN-ISO-ARTIFACTS-1")
            self.assertEqual(doc["artifact_count"],len(payload))
            self.assertEqual(rows["live/filesystem.squashfs"]["kind"],"root-filesystem-image")
            self.assertEqual(rows["boot/candidates/installer/installation.img"]["kind"],"ram-disk-image")
            self.assertEqual(rows["boot/koronos.elf"]["sha256"],hashlib.sha256(b"ELF").hexdigest())
            self.assertNotIn("boot/artifact-manifest.json",rows)
            self.assertTrue(sums.is_file())

    def test_missing_required_artifact_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);manifest=root/"manifest.json"
            result=subprocess.run([sys.executable,str(SCRIPT),"--root",str(root),"--manifest",str(manifest),
                                   "--require","boot/koronos.elf"],capture_output=True,text=True)
            self.assertEqual(result.returncode,2)
            self.assertIn("required ISO artifacts missing",result.stderr)
            self.assertFalse(manifest.exists())

    def test_builder_cannot_reuse_stale_iso_tree_or_package_marker(self):
        root=Path(__file__).resolve().parents[2]
        source=(root/"live-image/build.sh").read_text()
        self.assertIn('if [ ! -f "$BASE/.packages-installed-v3" ]',source)
        self.assertIn('touch "$BASE/.packages-installed-v3"',source)
        self.assertIn('rm -rf "$ISODIR"',source)
        self.assertIn('build_artifact_manifest.py',source)

if __name__=="__main__": unittest.main()
