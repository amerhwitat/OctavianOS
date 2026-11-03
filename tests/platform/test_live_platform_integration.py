import json
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class LivePlatformIntegrationTests(unittest.TestCase):
    def test_live_build_and_media_scripts_parse(self):
        for path in ("live-image/build.sh", "live-image/media/chimera-media-manager.sh"):
            subprocess.run(["bash", "-n", str(ROOT / path)], check=True)

    def test_runtime_manifests_are_valid(self):
        for path in (
            "platform/runtime/filesystem-capabilities.json",
            "platform/runtime/network-stack-manifest.json",
            "platform/runtime/koronos-architecture-profiles.json",
            "platform/runtime/third-party-sdk-manifest.json",
        ):
            with self.subTest(path=path):
                json.loads((ROOT / path).read_text(encoding="utf-8"))

    def test_root_account_is_locked_not_shared_password(self):
        script = (ROOT / "live-image/build.sh").read_text(encoding="utf-8")
        self.assertIn("passwd -l root", script)
        self.assertNotIn("root:live", script)

    def test_sdk_is_built_and_tested_before_image_composition(self):
        script = (ROOT / "live-image/build.sh").read_text(encoding="utf-8")
        self.assertIn("cmake --build /var/tmp/chimera-sdk-build", script)
        self.assertIn("ctest --test-dir /var/tmp/chimera-sdk-build", script)
        self.assertIn("sdk-build-status.json", script)

    def test_optical_media_is_read_only_and_usb_mounts_are_restricted(self):
        script = (ROOT / "live-image/media/chimera-media-manager.sh").read_text(encoding="utf-8")
        self.assertIn('opts="ro,nosuid,nodev,noexec"', script)
        self.assertIn('opts="rw,nosuid,nodev,noexec"', script)
        self.assertIn("auto_format:false", script) if "auto_format:false" in script else self.assertNotIn("mkfs", script)

    def test_live_build_does_not_claim_native_koronos_filesystems(self):
        docs = (ROOT / "docs/PLATFORM_RUNTIME_INTEGRATION.md").read_text(encoding="utf-8")
        self.assertIn("native Koronos VFS", docs)
        self.assertIn("not evidence", docs)


if __name__ == "__main__":
    unittest.main()
