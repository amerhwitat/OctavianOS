#pragma once
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Cooperative x86-64 kernel continuation ABI.
 *
 * This saves/restores the SysV callee-saved registers and a kernel RSP at a
 * call boundary. It is NOT a user trap frame and does NOT itself implement
 * scheduling, interrupt preemption, task lifetime, or user-mode return.
 * Both CR3 roots must keep the kernel code, context objects, TSS field, and
 * the selected kernel stack mapped before this primitive is enabled.
 */
enum { KORONOS_CONTEXT_FIRST_RUN = 1u };

typedef struct koronos_arch_task_context {
    uint64_t kernel_rsp;          /* 0: continuation return address at call boundary */
    uint64_t rbx;                 /* 8 */
    uint64_t rbp;                 /* 16 */
    uint64_t r12;                 /* 24 */
    uint64_t r13;                 /* 32 */
    uint64_t r14;                 /* 40 */
    uint64_t r15;                 /* 48 */
    uint64_t cr3;                 /* 56: physical PML4 root, low 12 bits clear */
    uint64_t kernel_stack_top;    /* 64: top of this task's owned ring-0 stack */
    uint64_t user_trap_frame;     /* 72: reserved for later trap/iret integration */
    uint64_t flags;               /* 80: KORONOS_CONTEXT_FIRST_RUN for synthetic entry */
} koronos_arch_task_context;

#if defined(__cplusplus)
static_assert(offsetof(koronos_arch_task_context, kernel_rsp) == 0, "context ABI: rsp");
static_assert(offsetof(koronos_arch_task_context, rbx) == 8, "context ABI: rbx");
static_assert(offsetof(koronos_arch_task_context, rbp) == 16, "context ABI: rbp");
static_assert(offsetof(koronos_arch_task_context, r12) == 24, "context ABI: r12");
static_assert(offsetof(koronos_arch_task_context, r13) == 32, "context ABI: r13");
static_assert(offsetof(koronos_arch_task_context, r14) == 40, "context ABI: r14");
static_assert(offsetof(koronos_arch_task_context, r15) == 48, "context ABI: r15");
static_assert(offsetof(koronos_arch_task_context, cr3) == 56, "context ABI: cr3");
static_assert(offsetof(koronos_arch_task_context, kernel_stack_top) == 64, "context ABI: stack");
static_assert(offsetof(koronos_arch_task_context, user_trap_frame) == 72, "context ABI: trap frame");
static_assert(offsetof(koronos_arch_task_context, flags) == 80, "context ABI: flags");
static_assert(sizeof(koronos_arch_task_context) == 88, "context ABI: size");
#else
_Static_assert(offsetof(koronos_arch_task_context, kernel_rsp) == 0, "context ABI: rsp");
_Static_assert(offsetof(koronos_arch_task_context, rbx) == 8, "context ABI: rbx");
_Static_assert(offsetof(koronos_arch_task_context, rbp) == 16, "context ABI: rbp");
_Static_assert(offsetof(koronos_arch_task_context, r12) == 24, "context ABI: r12");
_Static_assert(offsetof(koronos_arch_task_context, r13) == 32, "context ABI: r13");
_Static_assert(offsetof(koronos_arch_task_context, r14) == 40, "context ABI: r14");
_Static_assert(offsetof(koronos_arch_task_context, r15) == 48, "context ABI: r15");
_Static_assert(offsetof(koronos_arch_task_context, cr3) == 56, "context ABI: cr3");
_Static_assert(offsetof(koronos_arch_task_context, kernel_stack_top) == 64, "context ABI: stack");
_Static_assert(offsetof(koronos_arch_task_context, user_trap_frame) == 72, "context ABI: trap frame");
_Static_assert(offsetof(koronos_arch_task_context, flags) == 80, "context ABI: flags");
_Static_assert(sizeof(koronos_arch_task_context) == 88, "context ABI: size");
#endif

/*
 * Switch a cooperative kernel continuation. `old_context` is written before
 * switching; `next_context` must have a valid initialized kernel_rsp.
 * `tss_rsp0_slot` points to the active CPU's TSS.RSP0 field. Caller must
 * serialize this operation on that CPU and ensure all referenced memory is
 * mapped in both address spaces. Returns in the newly selected continuation.
 */
int koronos_arch_task_context_init(koronos_arch_task_context *context,
                                   void *stack_base, size_t stack_size,
                                   uint64_t cr3_root,
                                   void (*entry)(void *), void *argument);
void koronos_arch_context_switch(koronos_arch_task_context *old_context,
                                 const koronos_arch_task_context *next_context,
                                 uint64_t *tss_rsp0_slot);

#ifdef __cplusplus
}
#endif
