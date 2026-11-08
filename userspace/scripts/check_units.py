#!/usr/bin/env python3
"""Contract checks for the Aurora userspace units and helpers.

Validates the structure systemd itself tolerates but that silently breaks a
boot: missing sections, ExecStart pointing at a non-installed helper, unknown
WantedBy targets, and dangling instance units.
"""
from __future__ import annotations

import argparse
import configparser
import os
import sys
from pathlib import Path

SYSTEM_TARGETS = {"multi-user.target", "graphical.target", "basic.target", "sysinit.target",
                  "local-fs.target", "network-online.target", "default.target", "shutdown.target"}
SERVICE_SUFFIXES = (".service", ".target", ".socket", ".timer", ".mount")


def parse_unit(path):
    parser = configparser.ConfigParser(strict=False, interpolation=None, delimiters=("=",))
    parser.optionxform = str
    with open(path, encoding="utf-8") as handle:
        parser.read_file(handle)
    return parser


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--units", required=True)
    ap.add_argument("--helpers", required=True)
    args = ap.parse_args()

    errors = []
    unit_names = set()
    units = {}

    for name in sorted(os.listdir(args.units)):
        if not name.endswith(SERVICE_SUFFIXES):
            continue
        path = os.path.join(args.units, name)
        unit_names.add(name)
        try:
            parser = parse_unit(path)
        except Exception as exc:  # noqa: BLE001
            errors.append("%s: unparsable (%s)" % (name, exc))
            continue
        if not parser.has_section("Unit"):
            errors.append("%s: missing [Unit]" % name)
        elif not parser.get("Unit", "Description", fallback="").strip():
            errors.append("%s: missing Description=" % name)
        units[name] = parser

    helpers = {os.path.basename(p): p for p in
               (os.path.join(args.helpers, f) for f in os.listdir(args.helpers))
               if os.path.isfile(p)}
    for helper, path in helpers.items():
        if not os.access(path, os.X_OK):
            errors.append("%s: helper is not executable" % helper)

    for name, parser in units.items():
        service = parser["Service"] if parser.has_section("Service") else None
        if name.endswith(".service") and service is None:
            errors.append("%s: .service without [Service]" % name)
        if service is not None:
            exec_start = service.get("ExecStart", fallback="").strip()
            if not exec_start:
                errors.append("%s: missing ExecStart=" % name)
            else:
                binary = exec_start.split()[0].lstrip("-@+!:")
                base = os.path.basename(binary)
                if binary.startswith("/") and not os.path.exists(os.path.join(args.helpers, base)) \
                        and base not in ("startx", "openbox", "xsetroot", "feh", "xset", "ip", "sh", "python3"):
                    errors.append("%s: ExecStart binary is not provided by userspace/: %s" % (name, binary))
        if parser.has_section("Install"):
            for key in ("WantedBy", "RequiredBy"):
                value = parser.get("Install", key, fallback="")
                for target in value.split():
                    if target.endswith(".target") and target not in unit_names and target not in SYSTEM_TARGETS:
                        errors.append("%s: %s references unknown target %s" % (name, key, target))

    for parser_owner in ("jasper.target", "gates.target", "aurora.target", "marine.target"):
        if parser_owner not in units:
            errors.append("%s: desktop profile target is missing" % parser_owner)

    # The Xorg session is a real hosted-Linux desktop path. Validate the
    # boot-menu profile override and all four desktop profiles together so a
    # baked-in Aurora default cannot silently mask Jasper/Gates/Marine choices.
    repo_root = Path(__file__).resolve().parents[2]
    session_path = Path(args.helpers) / "aurora-session"
    shell_path = repo_root / "desktop/aurora-shell/assets/shell.js"
    image_builder = repo_root / "live-image/build.sh"
    try:
        session_text = session_path.read_text(encoding="utf-8")
        shell_text = shell_path.read_text(encoding="utf-8")
        builder_text = image_builder.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append("Xorg desktop profile contract: cannot read source (%s)" % exc)
    else:
        for profile in ("jasper", "gates", "aurora", "marine"):
            if profile not in session_text:
                errors.append("aurora-session: missing %s profile" % profile)
            if (profile + ": {") not in shell_text:
                errors.append("desktop shell: missing %s profile definition" % profile)
            if profile != "aurora" and (profile + ".target") not in unit_names:
                errors.append("userspace: missing %s.target" % profile)
        cmdline_pos = session_text.find('cmdline_profile="$(tr ')
        fallback_pos = session_text.find('for candidate in "$RUNTIME_FILE" "$PROFILE_FILE"; do')
        if cmdline_pos < 0 or fallback_pos < 0 or cmdline_pos > fallback_pos:
            errors.append("aurora-session: aurora.profile= boot argument must override baked-in profile files")
        if 'uri="${uri}${sep}profile=${profile}"' not in session_text:
            errors.append("aurora-session: selected profile is not passed to the desktop shell")
        for required in ("xserver-xorg-core", "xinit", "exec startx", "/usr/local/bin/aurora-session"):
            if required not in builder_text:
                errors.append("live-image: missing hosted Xorg session integration %s" % required)

    if errors:
        for err in errors:
            print("  FAIL %s" % err, file=sys.stderr)
        print("userspace check: FAILED (%d issue(s))" % len(errors), file=sys.stderr)
        return 1

    print("userspace check: OK -- %d units, %d helpers" % (len(units), len(helpers)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
