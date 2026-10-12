# OctavianOS source and application migration catalog

**Status: inventory and migration policy; not proof that source has been imported.**

Destination: https://github.com/amerhwitat/OctavianOS  
Primary OS source: https://github.com/amerhwitat/ChimeraIIOS

## Migration principles

- Preserve each source repository's Git history, license, notices, authorship, and upstream URL.
- Import source trees into distinct, named subtrees or Git-history refs before selectively integrating them. Do not flatten repositories together or overwrite files with matching names.
- Keep Aurora's product identity exactly **Aurora Wayland Glass Desktop**. Marine is a separate desktop environment and must not replace Aurora.
- Applications may be integrated only after identifying language/runtime, dependencies, license, security boundaries, data storage, and whether they are native, web-hosted, emulated, or compatibility-only.
- Do not claim a feature is ported or working until its build/test/launch path is validated.
- Avoid bundling secrets, credentials, private keys, generated build output, user data, and dependency caches.
- For large repositories, use Git fetch/mirror or a GitHub Actions workflow with a repository-scoped token; do not attempt to copy multi-gigabyte trees through individual file API calls.

## Repositories visible in the current GitHub account inventory

| Repository | Planned treatment | Status |
|---|---|---|
| [ChimeraIIOS](https://github.com/amerhwitat/ChimeraIIOS) | Primary OS, kernel, bootloader, drivers, ISA database, build system, installer, recovery, Aurora, tools, tests and documentation | History import blocked until `OCTAVIANOS_IMPORT_TOKEN` is configured |
| [amerhwitat.github.io](https://github.com/amerhwitat/amerhwitat.github.io) | Audit web applications and emulators; integrate source as apps or web app catalog entries | Not imported |
| [nlp](https://github.com/amerhwitat/nlp) | NLP/translation and language-processing applications; review model and dataset licenses | Not imported |
| [BizX](https://github.com/amerhwitat/BizX) | Business application candidate; isolate as an app/service and review dependencies/data handling | Not imported |
| [BizXtreme](https://github.com/amerhwitat/BizXtreme) | Large application candidate; preserve its independent history and inspect before integration | Not imported |
| [CPU4096](https://github.com/amerhwitat/CPU4096) | CPU/ISA research; compare against OctavianOS's N-bit execution model | Not imported |
| [CPU4096Simulator](https://github.com/amerhwitat/CPU4096Simulator) | Simulator application; integrate behind a desktop app manifest after dependency review | Not imported |
| [PDFreaderPY](https://github.com/amerhwitat/PDFreaderPY) | PDF reader application; package only after dependency and sandbox review | Not imported |
| [general](https://github.com/amerhwitat/general) | Inspect repository purpose and select relevant reusable assets | Not imported |
| [test](https://github.com/amerhwitat/test) | Inspect for useful source; do not import test data blindly | Not imported |
| [VanG](https://github.com/amerhwitat/VanG) | Private repository; access and license review required before import | Not imported |
| [eth-key-check](https://github.com/amerhwitat/eth-key-check) | Standalone utility candidate; security review required | Not imported |
| [bruteforce](https://github.com/amerhwitat/bruteforce) | Inspect purpose and safety constraints before any integration; isolate as a utility if appropriate | Not imported |
| [keygen](https://github.com/amerhwitat/keygen) | Inspect purpose and security implications before any integration | Not imported |

This is the account inventory returned during the current session, not a guarantee that it includes every repository or organization the account can access. Recheck the inventory before declaring the migration complete.

## Import phases

1. **Acquire:** configure the destination-only secret, fetch source branches/tags, verify object connectivity and exact source SHAs.
2. **Preserve:** keep source history under import refs; create a migration branch from the correct source commit rather than copying files manually.
3. **Inventory:** enumerate files by language, size, license, app entrypoint, build/test commands, generated assets, and target runtime.
4. **Reorganize:** group into boot/firmware, kernel, architecture/ISA, drivers, runtime, userspace, desktop shells, applications, SDK/toolchains, installer/recovery, tests, docs, and build/release.
5. **Integrate:** migrate one subsystem at a time; retain compatibility shims where old module names are ABI requirements.
6. **Validate:** compile/test by language and target, rebuild ISO/USB artifacts, inspect their manifests, and run QEMU boot/installer/recovery tests.
7. **Release:** record checksums, SBOM/dependency inventory, license notices, known limitations, and source commit mapping.

## Completion criteria

The migration is complete only when all intended source refs and app repositories have a recorded disposition; imported file counts and commit identities reconcile; no required source/assets are silently omitted; language-specific CI passes; and the destination's boot, installer, recovery, and desktop launch paths have runtime evidence. An inventory, scaffold, or successful Git push alone does not satisfy these criteria.
