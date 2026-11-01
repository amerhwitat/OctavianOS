# OctavianOS application integration

This directory is the integration target for applications migrated from owned repositories and the shared desktop application catalog.

## Cross-platform desktop application inventory

See [desktop-application-catalog.json](desktop-application-catalog.json) and the [searchable Application Center](application-center.html), linked from the web desktop preview. It indexes common desktop workflows and candidate applications across graphics/paint, photo editing, 3D, media playback and production, office/documents, communications, security, networking, engineering/CAD, games, emulation, development, and utilities. The inventory is intended to cover common user needs seen on Windows, Linux and macOS desktops without copying proprietary operating-system components.

**Catalog entries are not installed apps.** Every entry is currently `catalog-only` unless separately proven otherwise. An application is not considered integrated until source and license are reviewed, target architecture and dependencies are resolved, a reproducible package is built, permissions are reviewed, and launch/runtime tests pass on the intended target. Host-platform availability does not imply native bare-metal support.

## Import policy

- Preserve the source repository and license notices; record the exact source commit and license.
- Keep large or independent projects as isolated source modules until their build/runtime contracts are understood.
- Do not run untrusted imported code during inventory.
- Do not bundle secrets, private keys, credentials, user data, generated caches or unreviewed binaries.
- Each app must declare its runtime, architecture support, permissions, dependencies, launch method, health check and tests.
- Use least privilege and explicit file/network/device permissions. Shell strings from manifests must never be interpolated into a shell.
- Prefer native builds where available; otherwise clearly label web/PWA, VM, emulation, or compatibility-layer execution.
- Respect vendor licensing and distribution terms; proprietary applications must use official installers/stores or documented user-provided media.

## Completion rule

An app can be marked `supported` only after its source is present, license and dependencies are reviewed, its build/tests pass, its package is reproducible, and launch/permission behavior is tested in its intended runtime. Catalog, screenshots, package metadata, host compatibility, or a successful compile alone are insufficient.
