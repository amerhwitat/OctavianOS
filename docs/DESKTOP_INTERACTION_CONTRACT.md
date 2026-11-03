# Aurora and Marine desktop interaction contract

This change adds a shared interaction layer to the Aurora Wayland Glass and Marine
browser-desktop previews. It does not replace the GTK/Wayland native shell, a real file
manager, or the window compositor.

## Pointer behavior

- A single click selects a desktop shortcut.
- A deliberate second click on the selected shortcut's text starts inline rename.
- Double-click opens the selected shortcut.
- Right-click opens a context menu with Open, Rename, Properties, and Copy link.
- Shift+F10 opens the same context menu for the selected shortcut.
- Properties displays the preview item's label, destination and element type. It does not
  inspect or change host filesystem metadata or permissions.
- Renamed preview labels persist in browser local storage. They do not rename host files.

## Keyboard shortcuts implemented by the preview

| Shortcut | Action |
| --- | --- |
| F2 | Rename selected shortcut |
| Enter | Open selected shortcut |
| Shift+F10 | Open selected shortcut's context menu |
| Meta+Space | Toggle the Marine Start menu when present |
| Meta+E | Open the Files/Explorer shortcut when present |
| Ctrl+Alt+T | Open the Terminal shortcut when present |
| Escape | Dismiss context menu or Properties dialog |

These are a small shared preview subset, not a claim of complete Windows, macOS, Linux,
GNOME, KDE, or Finder shortcut parity. Native session adapters still need their own
platform-specific keymap, focus, accessibility and file-operation tests.

## Visual controls

The shared layer adds layered shadows, lift-on-hover and pressed-state depth to buttons and
shortcut cards, with visible keyboard focus and reduced-motion support. "3D" describes the
visual depth effect; no four-dimensional hardware or rendering capability is implied.

## VoiceConnect

Aurora and Marine receive a desktop entry and a launcher. The live-image builder installs
the launcher and both desktop entries. The launcher executes only a locally installed
VoiceConnect binary; if none is present, it opens the upstream project page. The optional
application catalog explicitly keeps installation and launchability unverified.

VoiceConnect's implementation and production acceptance remain in
[amerhwitat/test PR #8](https://github.com/amerhwitat/test/pull/8). The Windows renderer
click-diagnostics work is tracked in [PR #10](https://github.com/amerhwitat/test/pull/10).
Do not describe the app as production-ready until the renderer click gate, signing,
physical-device/network acceptance and independent review pass.

## Native integration still required

The browser previews are not the native Koronos desktop. The native GTK shell still needs
the same event routing connected to real compositor surfaces, a real VFS-backed file
manager, process-backed application launch, window-management actions, permission checks,
and end-to-end input/display tests before these interactions can be claimed in a bare-metal
Koronos session.
