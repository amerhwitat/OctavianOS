# Cataloged Applications and Runtimes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and integrate eligible applications, commands, and Python/Java utilities from the repositories referenced by the OS catalogs/manifests, with honest status for everything not yet packageable.

**Architecture:** Turn the current catalogs into a provenance-first source/build matrix. Preserve each repository's toolchain, license and architecture; make the optional package center expose only installed/build-verified items as launchable, with apt or a project package source used only where their signatures, hashes and rollback behavior are defined.

**Tech Stack:** JSON catalogs/schemas; C/C++; Python; Java/JVM; CMake; npm; Debian packages; GitHub Actions build matrices.

**Spec:** `docs/superpowers/specs/2026-11-03-production-first-vertical-slices-design.md`

## Global Constraints

- Scope is the two OS repositories, VoiceConnect, and app-bearing repositories referenced by current catalogs/manifests.
- Preserve source repository, pinned revision, license, build commands, dependencies, target architectures, package hash, and test status.
- Catalog-only, inaccessible, proprietary, or incompatible apps remain non-launchable and explicitly labeled; don't download/run unreviewed code.
- App install/update requires provenance verification, least privilege, safe argument handling, and rollback or a clear no-rollback disclosure.
- Native support is distinct from Linux-hosted, browser, VM, remote, or compatibility-layer execution.

## Review Focus

- Source revision disappears or changes — fail the reproducible fetch and preserve the recorded revision.
- License/redistribution limits conflict with ISO packaging — keep the app external/optional and link the official source.
- Missing runtime or architecture — disable launch and report the exact requirement.
- Package hash/signature mismatch — refuse installation.
- App attempts broad shell/filesystem/network access without a permission declaration — fail validation and deny launch.

---

### Task 1: Create a source-backed application/build matrix

**Files:**
- Create: `OctavianOS/apps/source-build-matrix.json`
- Modify: `OctavianOS/apps/app-manifest.schema.json`
- Modify: `OctavianOS/tests/test_optional_apps_catalog.py`
- Modify: `OctavianOS/.github/workflows/app-catalog-validation.yml`
- Mirror: `ChimeraIIOS` registry/catalog and validation workflow
- Sources: `amerhwitat/test/web/web_ui_manifest.json`, the VoiceConnect branch source tree, `apps/desktop-application-catalog.json`, and Chimera's app/command/Python/Java source catalogs

**Interfaces:**
- Consumes: Existing app catalogs and repository integrations.
- Produces: Per-app records with `source_repository`, `source_revision`, `license`, `language`, `runtime`, `architectures`, `build_workflow`, `package`, `launch_method`, and `evidence_status`.

- [ ] **Step 1: Add tests** for missing source revision/license, unsupported runtime, duplicate app ID, catalog-only status, and valid build-verified app metadata.
- [ ] **Step 2: Run** `python -m pytest -q tests/test_optional_apps_catalog.py` and Chimera's equivalent. Expected: new provenance cases fail.
- [ ] **Step 3: Implement matrix schema and inventory data** using only existing catalog/manifest repositories; mark absent sources and closed/unsupported runners as unavailable.
- [ ] **Step 4: Re-run** catalog tests and JSON validation. Expected: all statuses are internally consistent; no catalog-only entry can be marked installed/supported.
- [ ] **Step 5: Commit** the matrix and schema in both OS repositories.

### Task 2: Build and package first-party app batches

**Files:**
- Modify: `OctavianOS/apps/desktop-application-catalog.json`
- Modify: `OctavianOS/live-image/build.sh`
- Modify: `OctavianOS/apps/README.md`
- Modify: `ChimeraIIOS/desktop/aurora_app_registry.json`
- Modify: `ChimeraIIOS/desktop/optional_apps_catalog.json`
- Modify: `ChimeraIIOS/scripts/check_optional_apps_catalog.py`
- Modify: corresponding source package build workflows in the referenced repositories

**Interfaces:**
- Consumes: validated source/build matrix from Task 1.
- Produces: versioned OS package artifacts and app panel states `installed`, `optional-install`, `web`, `vm`, `remote`, `blocked`, or `catalog-only`.

- [ ] **Step 1: Add package validation tests** asserting exact pinned revision, license metadata, artifact checksum, architecture and launch target.
- [ ] **Step 2: Run** the app catalog and source pin validators. Expected: no current app lacking a built package can claim `installed`.
- [ ] **Step 3: Build source-backed applications** in native workflows for supported OS/architectures; use platform-specific runners for Windows/macOS packages and keep source artifacts separate from release packages.
- [ ] **Step 4: Re-run** package validation and install/launch smoke checks in disposable Linux images or platform runners.
- [ ] **Step 5: Commit** each independently verified app batch with source revision and package checksum.

### Task 3: Integrate commands and Python/Java utilities

**Files:**
- Modify: `ChimeraIIOS/web/command_catalog.json`
- Modify: `ChimeraIIOS/web/cli_catalog.json`
- Modify: `ChimeraIIOS/tools/commands/**`
- Modify: `OctavianOS/tools/chimera/**`
- Modify: referenced Python and Java source/test/build workflows identified in Task 1
- Create: shared command/runtime conformance tests in each OS repository

**Interfaces:**
- Consumes: command IDs, runtime declarations, and source matrix records.
- Produces: command dispatch via explicit argv arrays and Python/Java execution routes tied to installed/verified interpreters.

- [ ] **Step 1: Add failing command/runtime contract tests** for shell-injection strings, missing Python/JVM, unavailable command IDs, and successful allowlisted invocations.
- [ ] **Step 2: Run** the focused runtime/command tests in both repositories. Expected: invalid or unavailable launch targets are rejected.
- [ ] **Step 3: Implement dispatch and runtime capability display** using the existing command registries; never interpolate user input into a shell string.
- [ ] **Step 4: Re-run** command tests and build only the source-backed Python/Java modules whose declared runtime is installed in the target image.
- [ ] **Step 5: Commit** command/runtime batches with package and test evidence.

### Task 4: Add safe package manager and task manager surfaces

**Files:**
- Modify: `ChimeraIIOS/desktop/aurora_app_registry.json`
- Modify: `ChimeraIIOS/desktop/ui_command_registry.json`
- Modify: `OctavianOS/apps/desktop-application-catalog.json`
- Create: `OctavianOS/apps/package-actions.js`
- Create: `OctavianOS/apps/task-monitor.js`
- Create: matching source tests and session app panel wiring

**Interfaces:**
- Consumes: verified package source/index and process/service capability adapter for the actual backend.
- Produces: package actions that show source/version/hash and request elevation explicitly; `top`/`htop` launchers and a task list that report real processes or an explicit unsupported state.

- [ ] **Step 1: Add failing tests** for bad signature/hash, non-elevated installation, cancellation, missing backend, and fake task/process data.
- [ ] **Step 2: Run** the focused package/task manager tests. Expected: fake or unsafe operations are rejected.
- [ ] **Step 3: Implement** authenticated package operations and process list controls only for backends with real APIs; keep web previews read-only otherwise.
- [ ] **Step 4: Re-run** tests and exercise install/remove/cancel and task refresh against a disposable package root or mocked kernel boundary.
- [ ] **Step 5: Commit** the safe package/task manager surfaces and update image bundles.

