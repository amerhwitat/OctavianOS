import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class VendorSnapshotProvenanceTests(unittest.TestCase):
    def test_manifest_and_upstream_revision_match(self):
        vendor = ROOT / "vendor/chimera-ii-os"
        manifest = json.loads((vendor / "SNAPSHOT-MANIFEST.json").read_text(encoding="utf-8"))
        revision = (vendor / "UPSTREAM_REVISION").read_text(encoding="utf-8").strip()
        self.assertRegex(revision, r"^[0-9a-f]{40}$")
        self.assertEqual(manifest["source_commit"], revision)

    def test_manifest_labels_snapshot_as_source_only(self):
        manifest = json.loads((ROOT / "vendor/chimera-ii-os/SNAPSHOT-MANIFEST.json").read_text(encoding="utf-8"))
        self.assertIn("not yet a compiled or runtime-integrated port", manifest["scope"])
        self.assertIn("not current main", manifest.get("provenance_note", ""))


if __name__ == "__main__":
    unittest.main()
