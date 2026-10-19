# Desktop feature parity

Aurora remains **Aurora Wayland Glass Desktop**, with a macOS-inspired glass/dock direction. Marine is the Windows-inspired taskbar/launcher desktop. Both now load a shared, dependency-free browser-shell interaction layer for prototyping common desktop interactions and testing the feature contract.

Preview interactions include launcher search, window movement/focus/minimize/maximize/close, four virtual workspaces, window tiling, a dock/taskbar window switcher, quick settings, notification-center preview, persisted appearance/scale/accessibility preferences, keyboard shortcuts and a compatibility/help panel.

## Native implementation boundary

The pages are browser previews, not a native compositor or complete desktop runtime. They do not launch OS processes, expose a host shell, mount filesystems, enumerate real displays, manage audio/network/Bluetooth/power, or enforce native app permissions. `window.ChimeraDesktop.getCapabilities()` deliberately reports `nativeSessionAdapter: false` until the OS session manager and trusted adapters are implemented and tested.

The machine-readable `desktop/desktop-feature-contract.json` separates prototype features from the native work still required: process/session supervision, Wayland/X11/DRM/KMS, multi-monitor and HDR, file portals, peripheral services, power/session lifecycle, notifications, package/signature/sandboxing, clipboard/screen capture, assistive technology/IME/localization, secure credentials and compositor recovery.

Run `node --check desktop/shared/desktop-parity.js` and `python3 -m unittest discover -s tests/desktop -v` for preview checks. Native acceptance requires packaged artifacts and real session/runtime evidence for each supported host and bare-metal target. Do not claim full Windows/Linux/BSD/macOS feature parity from this prototype.
## Cross-platform application ecosystem

desktop/application-ecosystem.json is the shared discovery and integration catalog for common Windows, Linux and macOS desktop workflows: painting/image editing, media playback and creation, office/productivity, browsers/communication, games/emulators, development tools, archives and accessibility. It records upstream project URLs, platform scope, license notes and explicit implementation states. The catalog is broad, not exhaustive, and does not claim that catalog-only or proprietary apps are bundled or runnable.

The shared Aurora/Marine preview launcher now includes usable browser-local preview apps:
- **Paint Studio** — pointer drawing, color/brush controls and PNG export.
- **Media Player** — play a user-selected audio/video file with browser-supported codecs.
- **Image Viewer** — preview a user-selected image.
- **Game Center** — playable Tic-Tac-Toe and links to game projects.
- **Text Editor** — plain-text editing and .txt export.
- **Calculator** — basic arithmetic.
- **Desktop App Catalog** — browse upstream applications, platform targets and integration status.

Run `node --check desktop/shared/desktop-parity.js` and `python3 -m unittest discover -s tests/desktop -v`.

The GTK4 host-shell launcher also has fixed, allowlisted Linux host-command adapters for installed painting apps (Krita/GIMP/Pinta/KolourPaint), media players (VLC/mpv/Celluloid/Parole/Audacious), image viewers, game launchers, text editors, calculators and office suites. It checks each executable in PATH and reports when none is available; it does not invoke a shell or arbitrary user-supplied command. This is Linux host integration, not a Koronos-native launcher or a Windows/macOS runtime.\n\n**Important native boundary:** these built-in apps are browser-preview implementations. The catalog is not a package repository, third-party apps are not automatically installed, and a URL is not a native launch adapter. Native integration still requires target-specific packages/ports, dependency resolution, licensing and notices, MIME/open-with associations, process/session launch, sandbox/signature/update policy, accessibility, codec/graphics/input support and install/launch/quit tests. The new `application-ecosystem` acceptance gate remains `not_implemented` until retained target evidence proves those behaviors.
