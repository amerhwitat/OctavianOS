#!/bin/sh
# OctavianOS keyboard-only installer entry point.
# Deliberately delegates to the shared Chimera transaction frontend/backend;
# it must never implement a second, divergent installation path.
set -eu

if [ "$#" -gt 0 ] && [ "${1:-}" = "--help" ]; then
  cat <<'EOF'
Usage: text-installer.sh [SOURCE_ROOT [TARGET_ROOT]]

Delegates to the shared chimera-installer-cli. The frontend preserves its exit
status. A missing backend or an unsupported transaction is a hard failure.
EOF
  exit 0
fi

backend=""
if command -v chimera-installer-cli >/dev/null 2>&1; then
  backend=$(command -v chimera-installer-cli)
elif [ -x /usr/bin/chimera-installer-cli ]; then
  backend=/usr/bin/chimera-installer-cli
elif [ -x /usr/local/bin/chimera-installer-cli ]; then
  backend=/usr/local/bin/chimera-installer-cli
fi

if [ -z "$backend" ]; then
  echo "INSTALLATION BLOCKED: shared transactional installer backend is not installed." >&2
  echo "No disk changes were made; this wrapper does not substitute a shell-based installer." >&2
  exit 78
fi

exec "$backend" "$@"
