from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "koronos-userspace-acceptance.yml"


class KoronosUserspaceAcceptanceWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_installer_probe_stages_real_installer_media_contracts(self):
        self.assertIn("tools/chimera-stage-installer-media.sh", self.text)
        self.assertIn("busybox-static cpio", self.text)
        for module in (
            "chimera-installation-image",
            "chimera-installation-manifest",
            "chimera-installer-contract",
            "chimera-install-phases",
            "chimera-installer-profiles",
        ):
            self.assertIn(module, self.text)


if __name__ == "__main__":
    unittest.main()
