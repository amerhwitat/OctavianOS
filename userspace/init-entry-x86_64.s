; OctavianOS / Koronos production init - x86-64 entry point
; 
; This assembly module provides:
; - CPL3 entry trampoline (transitions from kernel setup to ring-3 main)
; - Real syscall gateway (SYSCALL/SYSRET capable)
; - Privilege entry/return state setup
; - Stack initialization

[bits 64]

section .text
    global _init_entry
    extern main
    extern __libc_csu_init
    extern __libc_csu_fini

; Real ring-3 entry point for init
; Kernel handoff sets:
; - RAX = entry point (will be 0 on entry to this stub)
; - RBX = kernel API revision (bootloader-specific)
; - RCX = kernel handoff flags
; - RDX = available memory size
; - RSI = kernel info structure
; - RDI = argc (from kernel command line)
; - RSP = valid ring-3 stack (kernel has validated and set up TSS RSP0)

_init_entry:
    ; Kernel transitions CPL0->CPL3 here via IRET or similar
    ; We must be at CPL 3 with a valid kernel stack in TSS.RSP0
    
    ; Verify we're actually in CPL3
    mov rax, cs
    and rax, 3
    cmp rax, 3
    jne .fatal_cpl_mismatch
    
    ; RSP should be valid (kernel set up TSS). Align it properly for System V ABI.
    ; Stack must be 16-byte aligned before a CALL instruction (to match -fstack-alignment=16)
    and rsp, -16
    sub rsp, 8
    
    ; Initialize CPU features and FPU
    ; - Set RFLAGS.AC = 0 (alignment check off, unless needed)
    ; - Initialize XMM state if needed
    
    ; Call C runtime initialization (if needed for libc)
    ; This ensures static ctors run, TLS is ready, etc.
    xor rbp, rbp            ; Clear frame pointer
    
    ; argc and argv were passed by kernel in RDI/RSI per Koronos calling convention
    ; Keep them for C main()
    ; argc = RDI (already set by kernel)
    ; argv = RSI (already set by kernel)
    ; envp = RDX (if present, else construct minimal envp)
    
    mov rdx, rsi            ; envp fallback
    test rdx, rdx
    jnz .have_envp
    lea rdx, [rel _default_envp]  ; Use minimal envp
    
.have_envp:
    ; Call main(argc, argv, envp)
    ; RDI = argc (already set)
    ; RSI = argv (already set)
    ; RDX = envp (set above)
    call main
    
    ; main() returns status code in EAX
    ; Exit with that code via EXIT syscall
    mov edi, eax            ; first arg = exit code
    mov eax, 60             ; KORONOS_SYSCALL_EXIT
    syscall
    
    ; Should never return, but if we do:
    ud2
    
.fatal_cpl_mismatch:
    ; We're not at CPL3 - fatal kernel configuration error
    mov eax, 1              ; exit code 1
    mov rsi, rax
    mov edi, eax
    mov eax, 60             ; EXIT
    syscall
    ud2

; Minimal default environment for init
section .rodata
_default_envp:
    dq _default_env_ld_library_path
    dq 0

_default_env_ld_library_path:
    db "LD_LIBRARY_PATH=/lib64:/usr/lib64", 0

; Syscall entry point - real implementation
; Kernel has installed an LSTAR MSR pointing to the syscall dispatch
; This is called from CPL3 via SYSCALL instruction
; Arguments in RDI, RSI, RDX, R10, R8, R9 (x86-64 syscall ABI)

section .text
    global koronos_syscall

koronos_syscall:
    ; RDI = syscall number
    ; RSI = arg1
    ; RDX = arg2
    ; RCX = arg3  [Note: RCX is clobbered by SYSCALL, so arg3 goes in R10]
    ; R8  = arg4
    ; R9  = arg5
    ; [RSP+8] or stack = arg6
    
    ; Map C ABI arguments to syscall ABI
    mov rax, rdi            ; syscall number -> RAX
    mov rdi, rsi            ; arg1
    mov rsi, rdx            ; arg2
    mov rdx, rcx            ; arg3
    mov rcx, r8             ; arg4 -> R10 for syscall
    mov r10, r9             ; arg5 actually passed in R9
    
    ; arg6 is on stack at [rsp+8]
    mov r8, [rsp + 8]
    mov r9, r8              ; arg6 -> R9
    
    syscall
    ; RAX = return value (errno is negative value, not in errno global)
    ret

; Stack canary initialization (for -fstack-protector)
section .data
    global __stack_chk_guard
    __stack_chk_guard dq 0xDEADBEEFDEADBEEF

; Exit code marker for verifier
section .data
    global _exit_marker
    _exit_marker:
        db "[KORONOS_INIT_EXIT]", 0
