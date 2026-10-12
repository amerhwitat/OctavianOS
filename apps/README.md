# OctavianOS application integration

This directory is the integration target for applications migrated from the owned repositories. Application source must be imported from its real upstream before it is listed as installed or supported.

## Import policy

- Preserve the source repository and license notices; record the exact source commit and license.
- Keep large or independent projects as isolated source modules until their build/runtime contracts are understood.
- Do not run untrusted imported code during inventory.
- Do not bundle secrets, private keys, credentials, user data, generated caches or unreviewed binaries.
- Each app must declare its runtime, architecture support, permissions, dependencies, launch method, health check and tests.
- Use least privilege and explicit file/network/device permissions. Shell strings from manifests must never be interpolated into a shell.
- Web apps and emulators may be hosted in a sandboxed web runtime; they are not native applications merely because they appear in the launcher.

## Initial candidates

See [the repository import catalog](../docs/REPOSITORY_IMPORT_CATALOG.md). Candidate projects include the web applications, NLP tools, CPU simulators, PDF reader, and business apps. They are **not imported or tested yet**.

## Completion rule

An app can be marked `supported` only after its source is present, license and dependencies are reviewed, its build/tests pass, its package is reproducible, and launch/permission behavior is tested in its intended runtime.
