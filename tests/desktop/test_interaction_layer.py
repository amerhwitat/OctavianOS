from pathlib import Path
import subprocess
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
            'Cut/Paste is disabled', 'Delete is disabled', 'e.key==="F4"',
            'oct-managed-window', 'oct-maximized', 'oct-minimized', 'arrangeWindows',
            'Tile Windows', 'Cascade Windows', 'AudioContext', 'e.detail===3',
            'Minimize', 'Maximize or restore', 'scrollbar-gutter:stable',
            'Toggle UI Sounds', 'soundEnabledKey', 'prefers-reduced-motion:reduce',
        ):
            self.assertIn(contract, source)

    def test_native_gtk_shell_is_bundled_and_has_real_window_controls(self):
        native = ROOT / "desktop/native/chimera-desktop-shell.cpp"
        self.assertTrue(native.is_file())
        source = native.read_text(encoding="utf-8")
        for contract in ("gtk_popover_menu_bar_new_from_model", "gtk_scrolled_window_new",
                         "gtk_gesture_click_new", "gtk_window_minimize", "gtk_window_maximize",
                         "canberra-gtk-play", "presses>=3"):
            self.assertIn(contract, source)
        build = (ROOT / "live-image/build.sh").read_text(encoding="utf-8")
        self.assertIn('NATIVE_SHELL_SRC="$PAY/repo/desktop/native/chimera-desktop-shell.cpp"', build)
        self.assertIn("xvfb-run -a /usr/local/bin/chimera-desktop-shell --desktop=aurora --self-test", build)
        self.assertIn("xvfb-run -a /usr/local/bin/chimera-desktop-shell --desktop=marine --self-test", build)
        self.assertIn("libcanberra-gtk3-module", build)

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
