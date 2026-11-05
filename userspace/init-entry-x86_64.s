/* Koronos x86-64 syscall veneer, GNU assembler / AT&T syntax.
 * The musl CRT owns process entry and initializes TLS/stdio before main().
 */
    .section .text
    .globl koronos_syscall
    .type koronos_syscall,@function
/* C ABI: (nr, a1, a2, a3, a4, a5, a6)
 * Koronos syscall ABI: RAX=nr, RDI=a1, RSI=a2, RDX=a3,
 * R10=a4, R8=a5, R9=a6.
 */
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

    .section .note.GNU-stack,"",@progbits
