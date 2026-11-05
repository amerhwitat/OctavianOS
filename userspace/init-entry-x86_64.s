/* OctavianOS / Koronos x86-64 init entry and syscall veneer.
 * GNU assembler, AT&T syntax. This source is compiled by GCC's ASM driver.
 */

    .section .text
    .globl _init_entry
    .type _init_entry,@function
    .extern main

/* Kernel must enter this symbol in CPL3 with a validated user stack.
 * Initial handoff ABI: RDI=argc, RSI=argv, RDX=envp (or NULL).
 */
_init_entry:
    xorl %ebp, %ebp

    /* Verify CPL3 before invoking any userspace code. */
    movw %cs, %ax
    andl $3, %eax
    cmpl $3, %eax
    jne .Lfatal_cpl_mismatch

    /* Preserve the supplied envp; construct an empty vector if absent. */
    testq %rdx, %rdx
    jne .Lhave_envp
    leaq _default_envp(%rip), %rdx
.Lhave_envp:
    /* SysV AMD64 requires RSP % 16 == 8 immediately before CALL. */
    andq $-16, %rsp
    subq $8, %rsp
    call main

    /* Koronos EXIT syscall. A successful exit never returns. */
    movl %eax, %edi
    movl $60, %eax
    syscall
    ud2

.Lfatal_cpl_mismatch:
    movl $1, %edi
    movl $60, %eax
    syscall
    ud2
    .size _init_entry, .-_init_entry

/* C ABI: (nr, a1, a2, a3, a4, a5, a6)
 * Koronos x86-64 syscall ABI: RAX=nr, RDI=a1, RSI=a2, RDX=a3,
 * R10=a4, R8=a5, R9=a6.
 */
    .globl koronos_syscall
    .type koronos_syscall,@function
koronos_syscall:
    movq %rdi, %rax
    movq %rsi, %rdi
    movq %rdx, %rsi
    movq %rcx, %rdx
    movq %r8,  %r10
    movq %r9,  %r8
    movq 8(%rsp), %r9
    syscall
    ret
    .size koronos_syscall, .-koronos_syscall

    .section .rodata
    .align 8
_default_envp:
    .quad 0

    .section .data
    .globl __stack_chk_guard
    .type __stack_chk_guard,@object
    .align 8
__stack_chk_guard:
    .quad 0x9e3779b97f4a7c15
    .size __stack_chk_guard, 8

    .globl _exit_marker
_exit_marker:
    .asciz "[KORONOS_INIT_EXIT]"

    .section .note.GNU-stack,"",@progbits
