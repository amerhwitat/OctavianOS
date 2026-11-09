#!/usr/bin/env python3
"""Verify every registered terminal/shell provider in the final target rootfs."""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

repo, root, payload = map(pathlib.Path, sys.argv[1:4])
registries = [repo / "aurora/terminals/registry.json", repo / "aurora/shells/registry.json"]
entries = [entry for path in registries for entry in json.loads(path.read_text(encoding="utf-8"))["entries"]]
ids = [entry["id"] for entry in entries]
if len(entries) != 28 or len(ids) != len(set(ids)):
    raise SystemExit(f"expected 28 unique terminal/shell providers, found {len(ids)}")
status_path = root / "usr/share/chimera/aurora/terminal-shell-provider-status.tsv"
statuses = {}
if status_path.is_file():
    for line in status_path.read_text(encoding="utf-8").splitlines():
        fields = line.split("\t")
        if len(fields) >= 3:
            statuses[fields[0]] = {"status": fields[1], "path": fields[2]}

installed_path = root / "usr/share/chimera/aurora/terminal-shell-installed.tsv"
if installed_path.is_file():
    for line in installed_path.read_text(encoding="utf-8").splitlines():
        fields = line.split("|")
        if len(fields) >= 5 and fields[2] == "source-built":
            statuses[fields[0]] = {
                "status": "source-built",
                "path": "/usr/local/bin/" + fields[1],
                "commit": fields[3],
                "sha256": fields[4],
            }

arch = subprocess.check_output(["chroot", str(root), "dpkg", "--print-architecture"], text=True).strip()
expected = {
    "amd64": "Advanced Micro Devices X86-64",
    "arm64": "AArch64",
    "armhf": "ARM",
    "i386": "Intel 80386",
    "riscv64": "RISC-V",
    "ppc64el": "PowerPC64",
    "s390x": "IBM S/390",
}.get(arch)
if not expected:
    raise SystemExit(f"unsupported target architecture for provider verification: {arch}")

verified, failures = [], []
shell_commands = {
    "bash": ["-c", "printf CHIMERA_SHELL_SMOKE"],
    "zsh": ["-c", "printf CHIMERA_SHELL_SMOKE"],
    "fish": ["-c", "printf CHIMERA_SHELL_SMOKE"],
    "dash": ["-c", "printf CHIMERA_SHELL_SMOKE"],
    "mksh": ["-c", "printf CHIMERA_SHELL_SMOKE"],
    "yash": ["-c", "printf CHIMERA_SHELL_SMOKE"],
    "elvish": ["-c", "echo CHIMERA_SHELL_SMOKE"],
    "nu": ["-c", "print CHIMERA_SHELL_SMOKE"],
}
for entry in entries:
    ident, binary = entry["id"], entry["binary"]
    item = statuses.get(ident)
    if not item or item["status"] == "unavailable":
        failures.append(f"{ident}: no installed or source-built provider")
        continue
    rel = item["path"]
    path = root / rel.lstrip("/")
    if not path.is_file():
        failures.append(f"{ident}: provider path missing in target rootfs: {rel}")
        continue
    if item.get("sha256"):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != item["sha256"]:
            failures.append(f"{ident}: source-built binary SHA-256 mismatch")
            continue
    header = subprocess.run(["readelf", "-h", str(path)], text=True, capture_output=True)
    if header.returncode == 0:
        machine = next((line.split(":", 1)[1].strip() for line in header.stdout.splitlines() if "Machine:" in line), "")
        if machine != expected:
            failures.append(f"{ident}: ELF machine {machine!r} does not match {arch}/{expected}")
            continue
        kind = "verified-elf"
    else:
        first = path.open("rb").readline(256).decode("utf-8", "replace").strip()
        if not first.startswith("#!"):
            failures.append(f"{ident}: provider is neither a target ELF nor an executable script")
            continue
        interpreter = first[2:].split()[0]
        if not (root / interpreter.lstrip("/")).exists():
            failures.append(f"{ident}: script interpreter missing: {interpreter}")
            continue
        kind = "verified-script"

    if entry["kind"] == "shell":
        args = shell_commands.get(binary, ["--version"])
        expected_output = b"CHIMERA_SHELL_SMOKE"
    else:
        args = ["-version"] if binary == "xterm" else ["--version"]
        expected_output = None
    try:
        probe = subprocess.run(["chroot", str(root), rel, *args], capture_output=True, timeout=15)
        output = probe.stdout + probe.stderr
        if probe.returncode != 0 or (expected_output and expected_output not in output):
            failures.append(f"{ident}: provider execution smoke failed (exit={probe.returncode})")
            continue
    except (OSError, subprocess.TimeoutExpired) as exc:
        failures.append(f"{ident}: provider execution smoke failed: {exc}")
        continue
    verified.append({
        "id": ident,
        "binary": binary,
        "kind": entry["kind"],
        "path": rel,
        "status": kind,
        "elf_machine": expected if kind == "verified-elf" else None,
        "runtime_status": "shell-command-smoke-pass" if entry["kind"] == "shell" else "version-smoke-pass",
        "source_commit": item.get("commit"),
        "sha256": item.get("sha256"),
    })

if failures:
    raise SystemExit("terminal/shell provider gate failed:\n" + "\n".join(failures))

verification = {
    "schema": "octavian-terminal-shell-provider-verification/v1",
    "target_architecture": arch,
    "required": len(entries),
    "verified": len(verified),
    "providers": verified,
    "runtime_launch_smoke": "shell command and terminal --version smoke tests passed; GUI launch/input not tested",
}
staging = {
    "schema": "AURORA-TERMINAL-SHELL-STAGING-2",
    "target_architecture": arch,
    "entries": verified,
    "policy": "Every listed provider is an installed target-architecture executable or script with a passing runtime smoke test.",
}
out_dir = root / "usr/share/chimera/aurora"
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "terminal-shell-provider-verification.json").write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
(out_dir / "terminal-shell-staging.json").write_text(json.dumps(staging, indent=2, sort_keys=True) + "\n", encoding="utf-8")
payload.mkdir(parents=True, exist_ok=True)
(payload / "terminal-shell-provider-verification.json").write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
(payload / "terminal-shell-staging.json").write_text(json.dumps(staging, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"Verified all {len(verified)} terminal/shell providers for {arch}; GUI input interaction remains untested.")
