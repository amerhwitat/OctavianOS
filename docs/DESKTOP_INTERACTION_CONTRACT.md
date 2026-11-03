# Aurora and Marine desktop interaction contract

## Shared interactions

Both Aurora and Marine browser previews load `desktop/shared/desktop-interactions.js` and provide File/Edit/View/Window/Help menus, desktop shortcut selection, delayed single-click rename, double-click open, triple-click Properties, right-click context menus, keyboard shortcuts and visible focus states.

## Window controls

- Preview windows expose Minimize, Maximize/Restore and Close/Hide controls.
- Minimized preview panels can be restored from the preview tray.
- Window menu actions arrange the page's visible panels in tiled or cascaded layouts.
- Resizable panels are viewport-bounded and provide horizontal/vertical scrollbars when content overflows.
- Window titlebar double-click toggles maximize/restore.

## Sounds and accessibility

- Short UI tones are synthesized only after a user interaction.
- The View menu provides a persistent UI-sound toggle.
- Reduced-motion preferences are respected and keyboard focus remains visible.

## Pointer behavior

- Single click selects.
- A deliberate second click on the selected label starts inline rename.
- Double-click opens.
- Triple-click opens Properties.
- Right-click or Shift+F10 opens Open/Rename/Properties/Copy Link.
- Preview rename stores a shortcut label only; it does not rename a host file.
- Delete and Cut/Paste remain blocked in the browser preview.

## Native-system boundary

The browser preview cannot control unrelated OS windows, the host taskbar, compositor workspaces, or host filesystem metadata. Native Wayland compositors own cross-application focus, resizing, tiling/cascading, virtual desktops and input policy. A native file manager must use the OS VFS and permission model. The GTK shell remains a host Linux userspace client, not a native Koronos compositor or shell session.
