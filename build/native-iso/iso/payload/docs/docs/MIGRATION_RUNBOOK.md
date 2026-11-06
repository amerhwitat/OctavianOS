# OctavianOS migration runbook

## Current state

- Destination: https://github.com/amerhwitat/OctavianOS
- Source: https://github.com/amerhwitat/ChimeraIIOS
- The first history-import attempt fetched and integrity-checked the source objects, but GitHub rejected the push because the Actions token cannot write workflow files.
- The importer is now manual-dispatch and requires the secret `OCTAVIANOS_IMPORT_TOKEN`.
- The N-bit register foundation is on branch `octavianos/nbit-foundation`; its host CI matrix passed at widths 1, 63, 64, 65, 128, 257, and 8192 bits.

## Enable the history import

Do not paste a token into a chat, issue, commit, or log.

1. In GitHub, create a fine-grained personal access token restricted to **OctavianOS** with **Contents: Read and write** and **Workflows: Read and write**. A classic token needs `repo` and `workflow` scopes.
2. Open OctavianOS → **Settings → Secrets and variables → Actions → New repository secret**.
3. Set the secret name to `OCTAVIANOS_IMPORT_TOKEN` and paste the token value into GitHub's secret form.
4. Open **Actions → Import ChimeraIIOS source history → Run workflow**.
5. Wait for the run to finish. Verify that `chimera-import/main`, `chimera-import/fix/boot-menu-target-routing`, `chimera-import/isa/verified-encoding-candidates-2026-10-12`, and `chimera-import/octavianos/identity-migration-2026-10-12` exist before proceeding.

The import keeps the bootstrap history on `octavianos/bootstrap`, preserves source branch history under `chimera-import/*`, and does not overwrite `main`.

## Promotion sequence after a successful import

1. Verify the imported branch SHAs match the source branch SHAs.
2. Promote the OctavianOS migration branch to `main`, retaining `octavianos/bootstrap` as a safety branch.
3. Open target-repository pull requests for boot routing and ISA metadata; rerun CI on the destination rather than reusing source-repository statuses.
4. Do not merge boot-routing work as a complete runtime handoff until installer userspace and recovery userspace demonstrably execute in QEMU.
5. Rebuild ISO, USB and container artifacts from the destination commit. Compare contents and checksums; do not rename stale artifacts.
6. Sweep references to ChimeraIIOS/Chimera II, update user-visible names, build paths, artifact labels and URLs, and retain legacy identifiers only for compatibility/provenance.
7. Keep the source repository untouched until the destination passes build, static validation, QEMU boot, installer/recovery, and release artifact acceptance.

## Security

The import token grants write access to workflow files and repository contents. Restrict it to this one repository, store it only as a GitHub Actions secret, rotate/revoke it after migration, and never print it in workflow logs.
