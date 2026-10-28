#include <stddef.h>
#include <stdint.h>
#include "chimera/task_context.h"

extern "C" void koronos_arch_task_bootstrap(void);

extern "C" int koronos_arch_task_context_init(
    koronos_arch_task_context *context,
    void *stack_base,
    size_t stack_size,
    uint64_t cr3_root,
    void (*entry)(void *),
    void *argument) {
    if (!context || !stack_base || !entry || stack_size < 256u) return -1;
    if (cr3_root == 0 || (cr3_root & 0xFFFu) != 0) return -2;

    const uintptr_t base = reinterpret_cast<uintptr_t>(stack_base);
    if (stack_size > static_cast<size_t>(UINTPTR_MAX - base)) return -3;
    const uintptr_t raw_top = base + stack_size;
    const uintptr_t top = raw_top & ~static_cast<uintptr_t>(0xFu);
    if (top < base || top - base < 128u) return -3;

    /* The first-run stack emulates a return into the bootstrap trampoline.
       The trampoline address is at top-16; top-8 is a non-return sentinel. */
    uintptr_t *frame = reinterpret_cast<uintptr_t *>(top - 16u);
    frame[0] = reinterpret_cast<uintptr_t>(&koronos_arch_task_bootstrap);
    frame[1] = 0;

    context->kernel_rsp = top - 16u;
    context->rbx = 0;
    context->rbp = 0;
    context->r12 = reinterpret_cast<uintptr_t>(entry);
    context->r13 = reinterpret_cast<uintptr_t>(argument);
    context->r14 = 0;
    context->r15 = 0;
    context->cr3 = cr3_root;
    context->kernel_stack_top = top;
    context->user_trap_frame = 0;
    context->flags = KORONOS_CONTEXT_FIRST_RUN;
    return 0;
}
