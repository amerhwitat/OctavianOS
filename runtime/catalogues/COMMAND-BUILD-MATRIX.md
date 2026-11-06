# Native command ISA build matrix

This CI job builds the actual native multicall source for three Linux ABI targets when the corresponding compiler is installed: x86-64, AArch64 and RV64. It validates the ELF machine field with `readelf`, records SHA-256 hashes, and creates symlink aliases only for the 15 names explicitly implemented in the native source policy.

The job deliberately does **not** claim support for all 104 ISA catalogue rows. MCU, GPU, VM, legacy, and other architectures require their own ABI, toolchain, syscall/runtime contract, and execution tests. Cross-compiled ELF output is not proof that Koronos boots or that commands execute correctly on target hardware. The manifest leaves runtime status as `not-tested-cross-build-only`.

The workflow uploads built outputs as CI artifacts; it does not check generated binaries into source control or silently ship foreign-architecture executables in the x86-64 ISO.
