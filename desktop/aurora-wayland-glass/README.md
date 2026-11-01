# Aurora Wayland Glass Desktop

Aurora's exact product name remains **Aurora Wayland Glass Desktop**. This directory contains a browser-based layout prototype for the macOS-inspired organization requested for the OctavianOS desktop. It is not the native Wayland compositor or the imported production Aurora implementation.

## Layout principles

- A slim global top menu/status bar.
- Glass-style windows and translucent surfaces.
- A centered dock for pinned/running applications.
- Finder-like file navigation and an application launcher.
- A clear distinction between application windows and the desktop background.
- Keyboard navigation, focus indicators, readable contrast, and a fallback wallpaper.

## Wallpaper

The prototype uses a remotely hosted Unsplash aurora-over-ocean photo. Source and license are documented in ../artwork/README.md and ../artwork/wallpapers.json. The production build should vendor and checksum approved wallpaper files through the existing artwork contract so the desktop works offline. Do not use the obsolete aurora-background.jpg scheme.

## Runtime status

Buttons demonstrate prototype interactions only. Native application launch, window management, compositor integration, and session readiness must be connected to OctavianOS userspace and verified before this desktop can be called production-ready.
