# Marine Desktop

Marine is a separate OctavianOS desktop environment, alongside **Aurora Wayland Glass Desktop**. This directory is the initial product scaffold, not a production compositor or a complete native desktop.

## Intended components

- Marine Shell: session shell and top-level window/panel orchestration.
- Marine Panel: application launcher, task list, status indicators and quick settings.
- Marine Settings: appearance, accessibility, display, network and session preferences.
- Marine Apps: app catalog with provenance, permissions, architecture and launch method.
- Marine Session Manager: validated session manifests, process supervision and fallback handling.

## Current implementation

`index.html` is a browser-based design/prototype for the desktop choice and Marine shell layout. It is not the Wayland compositor, native window manager, or boot-time session service. Native launch requires integration with OctavianOS's userspace and session manager.

## Names and interoperability

Aurora's name remains **Aurora Wayland Glass Desktop**. Users may choose Aurora or Marine when both are installed. Other Linux/Unix/Windows/macOS desktops should be listed only when a real compatible native, virtualized, remote, or compatibility-backed session is installed and passes its readiness probe.
