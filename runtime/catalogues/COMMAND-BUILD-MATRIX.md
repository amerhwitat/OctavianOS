# Native command Linux ABI build and execution matrix

The CI workflow compiles the real multicall source for eight Linux userspace ABIs: x86-64, i686, ARM EABI soft-float, AArch64, ARMv7 hard-float, RV64, PowerPC64LE and s390x. It checks each ELF machine field with `readelf`, records SHA-256 hashes, and creates aliases only for the 25 commands implemented in the shared native source. It then runs semantic smoke tests natively on x86-64 and under QEMU user-mode emulation for the seven foreign Linux ABIs.

The catalogue contains 854 unique commands across 971 platform entries. The native source implements 25 names; the other 829 names remain provider-required or unavailable until a real executable provider or implementation is staged and verified. A hosted Linux command binary is not a Koronos-native command implementation.

This matrix deliberately does **not** claim support for all 104 ISA catalogue rows or a Koronos kernel port for all eight Linux ABIs. MCU, GPU, VM, legacy and other architectures require their own ABI, toolchain, kernel/runtime contract, and conformance tests. QEMU user-mode validates Linux userspace behavior only; it does not prove Koronos boots or that its syscall ABI is compatible.

The workflow uploads target binaries, hashes and test manifests as CI artifacts. It does not check generated binaries into source control or silently ship foreign-architecture executables in the x86-64 ISO.
