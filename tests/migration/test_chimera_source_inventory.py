#!/usr/bin/env python3
"""Unit tests for the Chimera source inventory/content audit."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "migration" / "chimera-source-inventory.py"
SPEC = importlib.util.spec_from_file_location("chimera_source_inventory", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class InventoryTests(unittest.TestCase):
    def test_reports_missing_extra_and_different_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            upstream = root / "upstream"
            vendored = root / "vendored"
            upstream.mkdir()
            vendored.mkdir()
            (upstream / "kernel.c").write_text("upstream kernel", encoding="utf-8")
            (upstream / "docs").mkdir()
            (upstream / "docs" / "readme.md").write_text("docs", encoding="utf-8")
            (vendored / "kernel.c").write_text("stale kernel", encoding="utf-8")
            (vendored / "local.patch").write_text("patch", encoding="utf-8")

            report = MODULE.compare(upstream, vendored, "abc123")
            self.assertEqual(report["missing_from_vendor"], ["docs/readme.md"])
            self.assertEqual(report["extra_in_vendor"], ["local.patch"])
            self.assertEqual([item["path"] for item in report["different_content"]], ["kernel.c"])
            self.assertEqual(report["upstream_revision"], "abc123")
            self.assertFalse(report["history_compared"])
            self.assertFalse(report["build_or_boot_verified"])

    def test_ignores_git_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".git").mkdir()
            (root / ".git" / "config").write_text("metadata", encoding="utf-8")
            (root / "source.c").write_text("source", encoding="utf-8")
            self.assertEqual(set(MODULE.inventory(root)), {"source.c"})


if __name__ == "__main__":
    unittest.main()
