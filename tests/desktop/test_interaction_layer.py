from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class DesktopInteractionLayerTests(unittest.TestCase):
    def test_both_first_party_desktops_load_shared_interactions(self):
        pages = (
            ROOT / "desktop/aurora-wayland-glass/index.html",
            ROOT / "desktop/marine/index.html",
        )
        for page in pages:
            source = page.read_text(encoding="utf-8")
            self.assertIn('../shared/desktop-interactions.js', source, page.name)
            self.assertIn('VoiceConnect', source, page.name)

    def test_shared_javascript_parses(self):
        subprocess.run(["node", "--check", str(ROOT / "desktop/shared/desktop-interactions.js")], check=True)

    def test_shared_layer_exposes_requested_interactions_and_shortcuts(self):
        source = (ROOT / "desktop/shared/desktop-interactions.js").read_text(encoding="utf-8")
        for contract in (
            'contextmenu', 'dblclick', 'Properties', 'Rename',
            'e.key==="F2"', 'e.key==="Enter"', 'e.metaKey&&e.code==="Space"',
            'e.metaKey&&e.key.toLowerCase()==="e"', 'e.ctrlKey&&e.altKey',
            'showModal()', 'localStorage', 'menuDefinitions', 'runMenuAction',
        ):
            self.assertIn(contract, source)

    def test_voiceconnect_is_a_truthful_optional_launcher(self):
        launcher = (ROOT / "desktop/shared/voiceconnect-launcher.sh").read_text(encoding="utf-8")
        self.assertIn('[[ -n "$candidate" && -x "$candidate" ]]', launcher)
        self.assertIn('xdg-open "$url"', launcher)
        self.assertIn('VoiceConnect is not installed', launcher)
        build = (ROOT / "live-image/build.sh").read_text(encoding="utf-8")
        self.assertIn('octavian-voiceconnect-launcher', build)
        self.assertIn('octavian-voiceconnect-aurora.desktop', build)
        self.assertIn('octavian-voiceconnect-marine.desktop', build)


if __name__ == "__main__":
    unittest.main()
