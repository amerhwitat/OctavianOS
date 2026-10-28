#include <stddef.h>
#include <stdint.h>
#include "chimera/task_context.h"

/* Hosted test substitute; the real symbol is supplied by user_entry.asm. */
extern "C" void koronos_arch_task_bootstrap(void) {}

static void task_entry(void *) {}

int main(void) {
    if (sizeof(koronos_arch_task_context) != 88) return 1;
    if (offsetof(koronos_arch_task_context, cr3) != 56) return 2;
    if (offsetof(koronos_arch_task_context, kernel_stack_top) != 64) return 3;
    if (offsetof(koronos_arch_task_context, user_trap_frame) != 72) return 4;

    alignas(16) uint8_t stack[512]{};
    koronos_arch_task_context context{};
    int argument = 42;
    if (koronos_arch_task_context_init(&context, stack, sizeof(stack), 0x1000,
                                       task_entry, &argument) != 0) return 5;
    if (context.cr3 != 0x1000 || context.kernel_stack_top % 16 != 0) return 6;
    if (context.kernel_rsp % 16 != 0) return 7; /* first-run synthetic frame */
    if (context.flags != KORONOS_CONTEXT_FIRST_RUN) return 8;
    if (context.r12 != reinterpret_cast<uintptr_t>(&task_entry)) return 9;
    if (context.r13 != reinterpret_cast<uintptr_t>(&argument)) return 10;
    const uintptr_t *frame = reinterpret_cast<const uintptr_t *>(context.kernel_rsp);
    if (frame[0] != reinterpret_cast<uintptr_t>(&koronos_arch_task_bootstrap)) return 11;
    if (frame[1] != 0) return 12;

    if (koronos_arch_task_context_init(nullptr, stack, sizeof(stack), 0x1000,
                                       task_entry, &argument) != -1) return 13;
    if (koronos_arch_task_context_init(&context, stack, sizeof(stack), 0x1001,
                                       task_entry, &argument) != -2) return 14;
    if (koronos_arch_task_context_init(&context, stack, 64, 0x1000,
                                       task_entry, &argument) != -1) return 15;
    return 0;
}
