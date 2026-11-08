from __future__ import annotations
import json, os, subprocess, tempfile, unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "bin" / "aurora-session-manifest-check.py"

class SessionManifestCheckTests(unittest.TestCase):
    def run_check(self, root, profile):
        env = os.environ.copy()
        env["OCTAVIAN_SESSION_MANIFEST_DIR"] = str(root)
        return subprocess.run(["python3", str(SCRIPT), profile], env=env, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def valid(self, profile):
        return {
            "id": profile, "name": profile, "version": "0.1.0",
            "launch": {"executable": "/usr/local/bin/aurora-session", "args": ["--profile", profile]},
            "architectures": ["x86_64"], "display_backend": "x11",
            "requires": ["X.Org X Server", "Openbox", "WebKit2GTK"],
            "license": "OctavianOS first-party implementation",
            "readiness_probe": "pending:visible-window", "launch_method": "web", "status": "prototype"
        }

    def test_aurora_and_marine_manifests_validate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for profile in ("aurora", "marine"):
                (root / (profile + ".json")).write_text(json.dumps(self.valid(profile)), encoding="utf-8")
                result = self.run_check(root, profile)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_manifest_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.run_check(Path(tmp), "marine").returncode, 126)

    def test_manifest_id_and_launch_arguments_must_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = self.valid("marine")
            data["launch"]["args"] = ["--profile", "aurora"]
            (root / "marine.json").write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(self.run_check(root, "marine").returncode, 126)

    def test_jasper_and_gates_are_explicit_aurora_alias_profiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            for profile in ("jasper", "gates"):
                self.assertEqual(self.run_check(Path(tmp), profile).returncode, 0)

if __name__ == "__main__":
    unittest.main()
