#include <stddef.h>
#include <stdint.h>
#include "chimera/task_context.h"

int main(void) {
    if (sizeof(koronos_arch_task_context) != 88) return 1;
    if (offsetof(koronos_arch_task_context, cr3) != 56) return 2;
    if (offsetof(koronos_arch_task_context, kernel_stack_top) != 64) return 3;
    if (offsetof(koronos_arch_task_context, user_trap_frame) != 72) return 4;
    return 0;
}
