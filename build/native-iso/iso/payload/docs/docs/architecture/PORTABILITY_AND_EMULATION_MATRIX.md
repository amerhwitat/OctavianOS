# Portability and CPU-emulation acceptance matrix

This is a fail-closed engineering contract, not a claim that every RISC/CISC processor or phone is supported. The canonical machine-readable record is `architecture/support-matrix.json`.

## Current status

- **x86-64:** primary ISO architecture. The repository has target payload contracts and QEMU workflow scaffolding; production Live/Aurora, install/reboot, recovery diagnostics, and genuine SMP must be demonstrated by logs from actual staged payloads.
- **AArch64/mobile:** the mobile edition is an integration contract. A generic QEMU AArch64 boot would prove only the tested virtual machine, not any physical handset or tablet.
- **RISC-V 64:** a research/porting target until the architecture-specific kernel, interrupt/timer path, drivers and userspace are tested.
- **x86 32-bit, MIPS, PowerPC, LoongArch and other families:** research/emulation targets until the complete boot-to-userspace evidence exists.

## Do not conflate these execution modes

1. **Native:** the OS kernel executes on a matching physical CPU/board.
2. **Virtual machine:** an architecture-specific guest boots against a defined machine and firmware model.
3. **Instruction emulation:** a CPU emulator executes instructions from another ISA. This alone does not port the OS kernel or its drivers.
4. **OS/ABI compatibility:** translates system calls or userspace contracts; it is not hardware emulation.

## Target acceptance gates

For each advertised target, preserve the compiler/target triple, build flags, binary architecture, firmware/machine model, emulator version, serial logs and artifact hashes. Verify ELF machine/class/endianness/entry/load segments; boot the matching kernel; then require independent kernel, userspace, service and UI readiness markers.

Test memory permissions, interrupts, timer delivery, user-mode transition, scheduling, storage/network drivers and shutdown/recovery. SMP requires observed CPU-online IDs and concurrent per-CPU execution evidence, not merely a multi-vCPU launch flag.

Mobile additionally requires board-specific firmware/device-tree, display/touch/input, storage, audio/network as supported, suspend/resume, power management, verified updates and recovery. Unsupported targets must fail closed before loading an incompatible payload.

## Release rule

Only mark a target supported after all of its machine-readable `evidence_required` items have reproducible logs/artifacts attached. A source folder, menu entry, emulator catalog, successful compile, or QEMU machine existing upstream is not acceptance evidence.
