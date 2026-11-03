import pathlib
import unittest
ROOT = pathlib.Path(__file__).resolve().parents[2]
class AuroraWindowsGlassShellContract(unittest.TestCase):
    def test_shell_is_loaded_by_aurora_wayland_glass(self):
        page=(ROOT/"desktop/aurora-wayland-glass/index.html").read_text()
        self.assertIn("../shared/windows-glass-shell.js",page)
    def test_primary_surfaces_and_shortcuts_exist(self):
        source=(ROOT/"desktop/shared/windows-glass-shell.js").read_text()
        for token in ("ag-taskbar","ag-start","ag-quick","ag-notify","ag-taskview","File Explorer","Web Browser","Terminal","Applications","Settings","Brightness","Volume","virtualDesktop","ag-snap-left","ag-snap-right","Meta+Tab","ArrowLeft","ArrowRight","openQuickSettings","openNotifications","openTaskView"):
            self.assertIn(token,source)
    def test_native_backend_boundary_is_explicit(self):
        source=(ROOT/"desktop/shared/windows-glass-shell.js").read_text()
        self.assertIn("native service binding required",source)
        self.assertIn("compositor workspace binding required",source)
        self.assertIn("backend binding required",source)
if __name__=="__main__": unittest.main()
