#!/usr/bin/env sh
# OctavianOS terminal welcome banner. POSIX sh; no external dependencies.
[ "${CHIMERA_NO_COLOR:-0}" = 1 ] && color=0 || color=1
if [ "$color" = 1 ] && [ -t 1 ]; then
  cyan=$(printf '\033[1;36m'); violet=$(printf '\033[1;35m'); reset=$(printf '\033[0m')
else
  cyan=; violet=; reset=
fi
printf '%s' "$cyan"
cat <<'OCTAVIAN'
   ____   ____ _____ ___   ___    _    _   _  ___  ____
  / __ \ / ___|_   _/ _ \ / _ \  / \  | \ | |/ _ \/ ___|
 | |  | | |     | || | | | | | |/ _ \ |  \| | | | \___ \
 | |__| | |___  | || |_| | |_| / ___ \| |\  | |_| |___) |
  \____/ \____| |_| \___/ \___/_/   \_\_| \_|\___/|____/
OCTAVIAN
printf '%s' "$reset"
printf 'OctavianOS | Marine Desktop | Open • Secure • Infinite\n'
printf 'Open shells: bash, zsh, fish, dash, ksh, tcsh, yash, nushell, PowerShell*\n'
printf 'Terminals: Marine Terminal (native), plus installed compatible emulators\n'
printf 'Type "help" for commands. Optional providers are shown only when installed.\n'
printf '\n'
