#!/usr/bin/env python3
"""Keep Octavian's mirrored command catalogue, native policy and coverage aligned."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
catalog = json.loads((ROOT / "runtime/catalogues/commands/chimera-command-list.json").read_text(encoding="utf-8"))
policy = json.loads((ROOT / "runtime/catalogues/commands/compatibility-binary-policy.json").read_text(encoding="utf-8"))
coverage = json.loads((ROOT / "runtime/catalogues/commands/coverage.json").read_text(encoding="utf-8"))
fields = ("linux_bash", "macos_core", "windows_cmd_core", "powershell_core",
          "vbscript_core", "sql_server_core", "native_chimera")
names = {
    str(item.get("name") if isinstance(item, dict) else item).strip().casefold()
    for field in fields for item in catalog.get(field, [])
}
aliases = {str(x).casefold() for x in policy["native_build"]["multicall_aliases"]}
coverage_aliases = {str(x).casefold() for x in coverage["native_source_commands"]}
rows = {str(row["name"]).casefold(): row for row in coverage["commands"]}
assert len(names) == coverage["counts"]["unique_commands"]
assert coverage["counts"]["command_platform_entries"] == sum(len(catalog.get(f, [])) for f in fields)
assert aliases == coverage_aliases
assert aliases <= names
assert len(rows) == len(names)
for alias in aliases:
    assert rows[alias]["implementation"] == "native-source-implemented"
    assert rows[alias]["binary_status"] == "not-verified-in-repository"
print(f"PASS: {len(names)} mirrored commands, {len(aliases)} native source aliases, 104 ISA rows.")
