#ifndef CHIMERA_X86_64_CPU_H
#define CHIMERA_X86_64_CPU_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define CHIMERA_X86_64_CPU_ABI 1u
#define CHIMERA_X86_64_MAX_CPUS 16u
#define CHIMERA_X86_64_ENTRY_STACK_SIZE 16384u
#define CHIMERA_X86_64_KERNEL_CODE_SELECTOR 0x08u
#define CHIMERA_X86_64_KERNEL_DATA_SELECTOR 0x10u
#define CHIMERA_X86_64_USER_CODE_SELECTOR 0x1Bu
#define CHIMERA_X86_64_USER_DATA_SELECTOR 0x23u
#define CHIMERA_X86_64_TSS_SELECTOR 0x28u
#define CHIMERA_X86_64_CONTEXT_FRAME_SIZE 72u

typedef struct chimera_x86_64_context {
    uint64_t rsp;
    uint64_t cr3;
    uint64_t kernel_stack_top;
    uint32_t pid;
    uint32_t reserved;
} chimera_x86_64_context;

typedef struct __attribute__((packed)) chimera_x86_64_tss {
    uint32_t reserved0;
    uint64_t rsp0, rsp1, rsp2;
    uint64_t reserved1;
    uint64_t ist1, ist2, ist3, ist4, ist5, ist6, ist7;
    uint64_t reserved2;
    uint16_t reserved3;
    uint16_t io_map_base;
} chimera_x86_64_tss;

typedef struct __attribute__((packed)) chimera_x86_64_gdtr {
    uint16_t limit;
    uint64_t base;
} chimera_x86_64_gdtr;

static inline void chimera_x86_64_encode_tss_descriptor(
    uint64_t base, uint32_t limit, uint64_t *low, uint64_t *high) {
    if (!low || !high) return;
    *low = ((uint64_t)(limit & 0xFFFFu)) |
           ((base & 0xFFFFFFu) << 16) |
           (0x89ull << 40) |
           ((uint64_t)((limit >> 16) & 0x0Fu) << 48) |
           (((base >> 24) & 0xFFu) << 56);
    *high = base >> 32;
}

int chimera_x86_64_cpu_init(uint32_t cpu_id);
int chimera_x86_64_cpu_set_kernel_stack(uint32_t cpu_id, uint64_t stack_top);
int chimera_x86_64_cpu_is_ready(uint32_t cpu_id);
uint64_t chimera_x86_64_cpu_kernel_stack(uint32_t cpu_id);
uint64_t chimera_x86_64_cpu_bootstrap_kernel_stack(uint32_t cpu_id);
int chimera_x86_64_cpu_set_current_pid(uint32_t cpu_id, uint32_t pid);
uint32_t chimera_x86_64_cpu_current_pid(uint32_t cpu_id);
int koronos_x86_64_context_prepare(chimera_x86_64_context *context,
    uint64_t stack_base, uint64_t stack_size, uint64_t cr3,
    void (*entry)(void *), void *argument);
/* BSP-only handoff. Local cross-CR3 switching is allowed only while no AP is
 * online and the shared supervisor stack mapping is validated. AP-backed TLB
 * shootdowns and deferred reclamation remain unimplemented. */
int koronos_x86_64_context_switch(chimera_x86_64_context *from,
    const chimera_x86_64_context *to);

#ifdef __cplusplus
}
#endif
#endif
