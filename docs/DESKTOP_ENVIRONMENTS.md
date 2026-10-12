# OctavianOS desktop environments

## First-party desktop choices

- **Aurora Wayland Glass Desktop** — preserve this exact name and existing Aurora identity/artwork contract. This is the primary first-party desktop target.
- **Marine Desktop** — a separate first-party environment with its own shell, panel, application launcher, session configuration, accessibility preferences, and theme. Marine must not overwrite or rename Aurora assets.

The desktop chooser is a session preference, not a claim that every environment is already ported. It must show only sessions that are installed, compatible with the current architecture, and have a valid session entrypoint.

## External desktop choices

Linux/Unix desktops and Windows/macOS environments can be offered only through a supported execution route, such as a native port, container/VM, remote session, compatibility layer, or browser app. These routes have different hardware, licensing, API, and security constraints. A menu label is not equivalent to OS compatibility.

Potential Linux/Unix session adapters include desktops whose upstream licenses and dependencies permit redistribution. Windows and macOS require lawful, licensed system images and suitable virtualization/compatibility support; do not bundle proprietary system files or claim direct native execution on OctavianOS hardware without evidence.

## Session contract

Each installed session should provide a manifest with:
- stable ID and user-facing name;
- executable/session entrypoint and arguments;
- supported architectures and display backend;
- required services, graphics capabilities, packages, and permissions;
- package provenance, version, and license metadata;
- health/readiness probe and safe fallback session.

The session manager should validate manifests, escape arguments correctly, launch with a least-privilege user context, track exit status, and return to a known-good login/recovery UI if a session fails. Do not interpolate arbitrary user-controlled shell strings.

## Validation gates

1. Build/package the session.
2. Validate manifest and dependency resolution.
3. Start the session on a real supported compositor/display backend.
4. Confirm input, display scaling, accessibility, audio, clipboard, file dialogs and session shutdown.
5. Exercise missing dependency, GPU failure and crash recovery.
6. Record which features are native, compatibility-mediated, remote, or unavailable.
