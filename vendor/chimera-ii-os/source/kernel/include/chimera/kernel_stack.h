#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define KORONOS_KERNEL_STACK_ABI 1u
typedef struct koronos_kernel_stack {
    uint32_t slot;
    uint32_t generation;
    uint64_t base;
    uint64_t top;
} koronos_kernel_stack;
int koronos_kernel_stack_allocate(koronos_kernel_stack *out_stack);
int koronos_kernel_stack_release(const koronos_kernel_stack *stack);
int koronos_kernel_stack_self_test(void);
#ifdef __cplusplus
}
#endif
