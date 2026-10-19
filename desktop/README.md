# Desktop feature parity

Aurora remains **Aurora Wayland Glass Desktop**, with a macOS-inspired glass/dock direction. Marine is the Windows-inspired taskbar/launcher desktop. Both now load a shared, dependency-free browser-shell interaction layer for prototyping common desktop interactions and testing the feature contract.

Preview interactions include launcher search, window movement/focus/minimize/maximize/close, four virtual workspaces, window tiling, a dock/taskbar window switcher, quick settings, notification-center preview, persisted appearance/scale/accessibility preferences, keyboard shortcuts and a compatibility/help panel.

## Native implementation boundary

The pages are browser previews, not a native compositor or complete desktop runtime. They do not launch OS processes, expose a host shell, mount filesystems, enumerate real displays, manage audio/network/Bluetooth/power, or enforce native app permissions. `window.ChimeraDesktop.getCapabilities()` deliberately reports `nativeSessionAdapter: false` until the OS session manager and trusted adapters are implemented and tested.

The machine-readable `desktop/desktop-feature-contract.json` separates prototype features from the native work still required: process/session supervision, Wayland/X11/DRM/KMS, multi-monitor and HDR, file portals, peripheral services, power/session lifecycle, notifications, package/signature/sandboxing, clipboard/screen capture, assistive technology/IME/localization, secure credentials and compositor recovery.

Run `node --check desktop/shared/desktop-parity.js` and `python3 -m unittest discover -s tests/desktop -v` for preview checks. Native acceptance requires packaged artifacts and real session/runtime evidence for each supported host and bare-metal target. Do not claim full Windows/Linux/BSD/macOS feature parity from this prototype.
