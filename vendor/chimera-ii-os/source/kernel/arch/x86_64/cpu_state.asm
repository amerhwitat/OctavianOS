BITS 64
section .text
global koronos_x86_64_load_gdt_tss
koronos_x86_64_load_gdt_tss:
    lgdt [rdi]
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov ss, ax
    push qword 0x08
    lea rax, [rel .reload_cs]
    push rax
    retfq
.reload_cs:
    mov ax, si
    ltr ax
    ret

; C wrapper validates the shared stack mapping and performs the BSP-only
; CR3/TSS.RSP0/PID handoff. The raw primitive verifies the target CR3 is active.
global koronos_x86_64_context_switch_raw
koronos_x86_64_context_switch_raw:
    test rdi, rdi
    jz .invalid
    test rsi, rsi
    jz .invalid
    cmp rdi, rsi
    je .same
    mov rax, [rsi]
    test rax, rax
    jz .invalid
    mov rcx, [rsi + 8]
    test rcx, rcx
    jz .invalid
    test rcx, 0xFFF
    jnz .invalid
    mov rdx, cr3
    cmp rcx, rdx
    jne .space_mismatch
    pushfq
    cli
    push rbp
    push rbx
    push r12
    push r13
    push r14
    push r15
    ; The wrapper stored the outgoing CR3 before activating the target root.
    mov [rdi], rsp
    mov rsp, rax
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbx
    pop rbp
    popfq
    xor eax, eax
    ret
.same:
    xor eax, eax
    ret
.space_mismatch:
    mov eax, -2
    ret
.invalid:
    mov eax, -1
    ret

global koronos_x86_64_context_trampoline
koronos_x86_64_context_trampoline:
    mov rdi, r12
    sub rsp, 8
    call r13
    add rsp, 8
    ud2
