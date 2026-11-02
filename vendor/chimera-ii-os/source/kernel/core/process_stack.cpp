#include "chimera/process_stack.h"
#include "chimera/process.h"
extern "C" int chimera_process_create_kernel_stack(uint32_t pid) {
    if (!pid) return -1;
    koronos_kernel_stack stack{};
    if (koronos_kernel_stack_allocate(&stack) != 0) return -2;
    if (chimera_process_attach_kernel_stack(pid, &stack) != 0) {
        (void)koronos_kernel_stack_release(&stack); return -3;
    }
    return 0;
}
extern "C" int chimera_process_release_kernel_stack(uint32_t pid) {
    if (!pid) return -1;
    koronos_kernel_stack stack{};
    if (chimera_process_detach_kernel_stack(pid, &stack) != 0) return -2;
    if (koronos_kernel_stack_release(&stack) != 0) {
        (void)chimera_process_attach_kernel_stack(pid, &stack); return -3;
    }
    return 0;
}
