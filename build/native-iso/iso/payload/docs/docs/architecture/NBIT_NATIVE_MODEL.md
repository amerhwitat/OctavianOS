# OctavianOS native N-bit foundation

## Contract

- Default register width is **8192 bits**.
- Set `OCTAVIAN_NBIT_WIDTH=N` at compile time to select another positive width.
- Values use little-endian arrays of 64-bit limbs and are normalized so bits at or above N are always zero.
- Unsigned add/subtract wrap modulo (2^N).
- Logical shifts by N or more yield zero.
- Operations accept aliased output/input pointers; null pointers are no-ops for mutation functions.
- The code is freestanding-friendly C11 and does not require compiler-specific 128-bit integer types.

## Current scope

This is a tested *register-value substrate*, not a complete CPU or ISA. It does not yet implement signed interpretation, overflow/carry flag policy, multiplication/division, atomic operations, virtual addresses, memory ordering, traps, privilege transitions, vector/FPU state, instruction decode/execute, or a scheduler context. Those semantics must be defined by an architecture profile and implemented/tested separately.

The 8192-bit mode is software-defined. Real x86-64/Arm/RISC-V CPUs do not directly execute arbitrary 8192-bit instructions; a backend must lower multi-limb operations, emulate instructions, or return an explicit unsupported/trap status.

## Host test

Compile the same test at multiple widths:

```sh
cc -std=c11 -Wall -Wextra -Werror -pedantic -Iinclude tests/nbit/test_nbit.c -o /tmp/octavian-nbit-8192
/tmp/octavian-nbit-8192
cc -std=c11 -Wall -Wextra -Werror -pedantic -DOCTAVIAN_NBIT_WIDTH=128 -Iinclude tests/nbit/test_nbit.c -o /tmp/octavian-nbit-128
/tmp/octavian-nbit-128
cc -std=c11 -Wall -Wextra -Werror -pedantic -DOCTAVIAN_NBIT_WIDTH=257 -Iinclude tests/nbit/test_nbit.c -o /tmp/octavian-nbit-257
/tmp/octavian-nbit-257
```

Passing these host tests proves only the fixed-width value operations exercised here; it does not establish kernel integration or ISA conformance.
