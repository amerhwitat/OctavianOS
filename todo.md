# OctavianOS — Request B Execution Plan

## A. App Conversion & Packaging
- [x] Repo/app inventory -> desktop/repo_app_catalog.json (309 apps)
- [x] Python CLI -> GUI (38 launchers + universal octavian_app_runner)
- [x] PyInstaller one-file builds (8 binaries in apps/bin/)
- [ ] Fix chimera-runtime PyInstaller relative-import failure
- [x] Java sources -> runnable jars (23 in apps/java/dist/)
- [ ] Java .desktop launchers + staging

## B. Desktop Experience
- [x] Shared os-features.js (sounds, mouse, keyboard, windows, lock, palette)
- [x] Inject feature layer into Aurora + Marine
- [x] 24-app default suite (apps/default-suite.html)
- [ ] Dock/menu integration for default suite + repo apps
- [ ] Linux shells/desktops/terminals catalogue + source tarballs

## C. Web Surfaces
- [x] Repo App Explorer (repos/index.html, 3541 files staged)
- [ ] Node.js app exposure (BizX, BizXtreme, threejs, Thamudic, gh-pages apps)
- [ ] Cockpit-like Octavian Console (apps/octavian-console.html + backend)
- [ ] System-user authentication (PAM) for console + desktop session

## D. Rootfs & ISO
- [ ] Language toolchains in rootfs (python3, JRE17, node, gcc, rustc, go, php, ruby, perl, lua)
- [ ] Stage apps/bin, apps/java, repo-gui, sources into rootfs
- [ ] Rebuild ISO via build-chimera-iso.sh --host-rootfs
- [ ] QEMU boot verification of all new surfaces
- [ ] Docs, SHA256SUMS, release notes, publish
