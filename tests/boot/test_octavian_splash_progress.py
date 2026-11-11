#!/usr/bin/env python3
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PROGRESS = ROOT / "tools/boot/octavian-progress.sh"
ARTWORK = ROOT / "boot/splash/octavian-octopus-background.svg"
ARTWORK_CONTRACT = ROOT / "boot/splash/artwork-contract.json"
VIDEO_TOOL = ROOT / "tools/artwork/rebrand-init-video.sh"
OSD = ROOT / "tools/boot/octavian-progress-osd.lua"
SPLASH = ROOT / "tools/boot/octavian-init-splash.sh"
SPLASH_UNIT = ROOT / "boot/splash/octavian-init-splash.service"
WORKFLOW = ROOT / ".github/workflows/octavian-splash.yml"


class OctavianSplashProgressTests(unittest.TestCase):
    def test_progress_is_event_driven_and_monotonic(self):
        with tempfile.TemporaryDirectory() as temp:
            env = os.environ.copy()
            env["OCTAVIAN_PROGRESS_DIR"] = temp
            subprocess.run(["bash", str(PROGRESS), "start", "Kernel", "Started"], env=env, check=True, capture_output=True, text=True)
            subprocess.run(["bash", str(PROGRESS), "phase", "25", "Drivers", "Drivers initialized"], env=env, check=True, capture_output=True, text=True)
            blocked = subprocess.run(["bash", str(PROGRESS), "phase", "10", "Backwards", "Must fail"], env=env, capture_output=True, text=True)
            self.assertEqual(blocked.returncode, 3)
            state = (Path(temp) / "progress.state").read_text()
            self.assertIn("percent=25", state)
            self.assertIn("phase=Drivers", state)
            subprocess.run(["bash", str(PROGRESS), "complete", "Userspace", "Session ready"], env=env, check=True, capture_output=True, text=True)
            final = (Path(temp) / "progress.state").read_text()
            self.assertIn("percent=100", final)
            self.assertIn("status=complete", final)

    def test_new_session_can_reset_old_completed_state(self):
        with tempfile.TemporaryDirectory() as temp:
            env = os.environ.copy()
            env["OCTAVIAN_PROGRESS_DIR"] = temp
            subprocess.run(["bash", str(PROGRESS), "complete"], env=env, check=True, capture_output=True, text=True)
            subprocess.run(["bash", str(PROGRESS), "start"], env=env, check=True, capture_output=True, text=True)
            self.assertIn("percent=0", (Path(temp) / "progress.state").read_text())

    def test_octopus_artwork_and_menu_contract_are_present(self):
        svg = ARTWORK.read_text(encoding="utf-8")
        contract = json.loads(ARTWORK_CONTRACT.read_text(encoding="utf-8"))
        self.assertIn("OCTAVIANOS", svg)
        self.assertIn("tentacle", svg)
        self.assertEqual(contract["brand"], "OctavianOS")
        self.assertEqual(contract["progress_semantics"], "Progress is driven by completed initialization/install events, never by elapsed time or static menu echoes.")
        for menu in ["boot/iso/grub.cfg", "boot/jasper/jasper.cfg", "boot/jasper/live.cfg", "boot/jasper/install.cfg", "boot/jasper/recovery.cfg", "boot/jasper/diagnostics.cfg", "boot/jasper/retro.cfg", "boot/jasper/safe.cfg", "boot/spitfire/spitfire-menu.cfg", "boot/installation/menu.cfg"]:
            self.assertIn("/boot/grub/octavian-octopus-background.png", (ROOT / menu).read_text(encoding="utf-8"))

    def test_video_rebrand_keeps_live_progress_separate(self):
        script = VIDEO_TOOL.read_text(encoding="utf-8")
        osd = OSD.read_text(encoding="utf-8")
        self.assertIn("OCTAVIANOS", script)
        self.assertIn("mp.set_osd_ass(0, 0", osd)
        self.assertIn("progress differs by installer", script)
        self.assertIn("progress.state", osd)

    def test_init_video_is_hardcoded_and_live_progress_osd_is_staged(self):
        script = SPLASH.read_text(encoding="utf-8")
        unit = SPLASH_UNIT.read_text(encoding="utf-8")
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("/boot/splash/Init-OctavianOS.mp4", script)
        self.assertIn("/run/octavian/progress.state", script)
        self.assertIn("--script=", script)
        self.assertIn("ExecStart=/usr/bin/octavian-init-splash --background", unit)
        self.assertIn("octavian-init-splash.sh", workflow)
        self.assertIn("Init-OctavianOS.mp4", workflow)


if __name__ == "__main__":
    unittest.main()
