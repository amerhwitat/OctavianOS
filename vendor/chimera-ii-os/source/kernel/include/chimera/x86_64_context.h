#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct koronos_x86_64_context {
    uint64_t rsp;
    uint64_t cr3;
} koronos_x86_64_context;

#define KORONOS_X86_64_CONTEXT_FRAME_SIZE 72u

/* Prepare a first-entry kernel frame in caller-owned mapped memory. The caller
 * must supply a process-owned stack with an unmapped guard page. */
int koronos_x86_64_context_prepare(koronos_x86_64_context *context,
                                   uint64_t stack_base, uint64_t stack_size,
                                   uint64_t cr3, void (*entry)(void *), void *argument);

/* Save/restore callee-saved registers, RFLAGS and CR3. Cross-CR3 switches are
 * refused until supervisor mappings are shared and TLB shootdowns exist. */
int koronos_x86_64_context_switch(koronos_x86_64_context *from,
                                  const koronos_x86_64_context *to);

#ifdef __cplusplus
}
#endif
