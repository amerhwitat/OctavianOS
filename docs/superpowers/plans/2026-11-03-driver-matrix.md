# Declared Hardware Driver Matrix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing driver catalogs and native driver code into a validated, device-specific support matrix, then build and exercise the declared QEMU baseline before expanding physical-device coverage.

**Architecture:** Start from tracked driver implementations, source provenance, current ISO kernel, and QEMU machine devices. Represent each device/driver/function with compile, load, and runtime evidence. Prioritize virtual devices used by CI; do not mark every catalog entry as a working driver.

**Tech Stack:** C/C++; CMake; Python JSON validators; PCI/virtio; QEMU; GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-03-production-first-vertical-slices-design.md`

## Global Constraints

- Driver claims are per device ID, target architecture, kernel/backend, and supported function.
- Preserve upstream source provenance, license, signing status, and redistributability.
- Build success is distinct from load and hardware/runtime validation.
- x86_64 QEMU support does not prove ARM64 mobile or physical-device support.
- Never download/load an unpinned third-party driver or firmware blob during tests.
- Production release support remains false until the required boot, storage, networking, input/display, and recovery matrix passes.

## Review Focus

- Driver source is absent or license unclear — report inventory-only and refuse build/staging.
- Device ID/architecture mismatch — reject driver binding.
- Driver compiles but cannot load/initialize — remain build-verified only.
- QEMU device absent — mark runtime check skipped, not passed.
- Firmware/proprietary blob required — require an explicit user-supplied or distributable source and checksum.

---

### Task 1: Reconcile driver source and target matrix

**Files:**
- Modify: `OctavianOS/architecture/support-matrix.json`
- Modify: `OctavianOS/vendor/chimera-ii-os/source/drivers/driver-manifest.json`
- Modify: `OctavianOS/vendor/chimera-ii-os/source/drivers/hardware-driver-catalog.json`
- Modify: `OctavianOS/vendor/chimera-ii-os/source/drivers/hardware-driver-policy.json`
- Modify: `OctavianOS/vendor/chimera-ii-os/source/config/drivers/driver-repositories.json`
- Modify: `OctavianOS/vendor/chimera-ii-os/source/config/drivers/driver-policy.json`
- Mirror: corresponding `ChimeraIIOS/drivers/**`, `config/drivers/**`, and architecture docs
- Create: `OctavianOS/architecture/driver-runtime-matrix.json`

**Interfaces:**
- Consumes: driver registries, source catalogs and supported architectures.
- Produces: device records with vendor/device ID, bus, architecture, source/license, implemented functions, build status, load status, and runtime evidence.

- [ ] **Step 1: Add validator tests** for duplicate IDs, unknown devices, missing source/license, inconsistent platform support, and catalog-only driver claims.
- [ ] **Step 2: Run** existing driver acquisition/policy tests and new matrix tests. Expected: contradictory or unproven driver records fail.
- [ ] **Step 3: Reconcile the matrix** from tracked C/C++/Rust/Kotlin/Java adapters and available device IDs; keep planned/acquisition records distinct from kernel driver implementation.
- [ ] **Step 4: Re-run** matrix/schema validation. Expected: every supported claim links to source and a real build/runtime workflow.
- [ ] **Step 5: Commit** the driver matrix and validator in both OS repositories.

### Task 2: Build the CI virtual hardware baseline

**Files:**
- Modify: tracked `kernel/drivers/builtin/virtio.cpp`, `pci-generic.cpp`, and `pc-display.cpp` only where existing failing evidence identifies a missing path
- Modify: `OctavianOS/tests/qemu/README.md`
- Modify: native kernel and QEMU workflows in both OS repositories
- Create: device-level trace tests under existing `tests/qemu/`

**Interfaces:**
- Consumes: driver matrix record and QEMU machine/device definition.
- Produces: device trace with PCI ID, selected driver, initialization state, exposed block/network/display/input function, and failure code.

- [ ] **Step 1: Add failing QEMU tests** for absent/present storage, network, display, console, and input devices; require an explicit unsupported state when a device is absent.
- [ ] **Step 2: Run** the QEMU driver workflow on the current kernel. Expected: report exact failing device/initialization paths without upgrading catalog status.
- [ ] **Step 3: Implement or repair** only the x86_64 virtual devices declared in the matrix; validate device IDs before binding and clean up on initialization failure.
- [ ] **Step 4: Re-run** build and QEMU tests. Expected: trace proves each required virtual device initialized and exposed the expected function.
- [ ] **Step 5: Commit** driver changes with trace artifacts.

### Task 3: Add regression coverage and expand device support in verified batches

**Files:**
- Modify: driver matrix and source manifests in both OS repositories
- Modify: corresponding kernel driver source/tests and CI matrix
- Modify: `docs/CHIMERA_HARDWARE_DRIVERS.md` and `architecture/support-matrix.json`

**Interfaces:**
- Consumes: accepted virtual device baseline from Task 2.
- Produces: per-batch supported-device list and build/load/runtime artifacts.

- [ ] **Step 1: Add a test per newly supported hardware family** for supported revision, architecture mismatch, init failure, and shutdown/recovery behavior.
- [ ] **Step 2: Run** target-specific build and QEMU/physical-device workflow. Expected: no support change for cases without evidence.
- [ ] **Step 3: Implement** the next source-backed driver batch using approved provenance/licensing and existing kernel APIs.
- [ ] **Step 4: Re-run** all matrix tests, kernel builds, and available hardware checks.
- [ ] **Step 5: Commit** each accepted driver batch and update supported device evidence; leave untested hardware marked planned/unsupported.

