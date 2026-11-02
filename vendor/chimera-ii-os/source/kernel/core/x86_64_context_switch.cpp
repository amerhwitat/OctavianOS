#include "chimera/x86_64_cpu.h"
#include "chimera/address_space.h"
namespace {
static bool canonical(uint64_t address) {
    return (address >> 47) == 0 || (address >> 47) == 0x1FFFFu;
}
}
extern "C" int koronos_x86_64_context_switch_raw(
    chimera_x86_64_context *from, const chimera_x86_64_context *to);
extern "C" int koronos_x86_64_context_switch(
    chimera_x86_64_context *from, const chimera_x86_64_context *to) {
    if (!from || !to || from == to || !to->rsp ||
        !chimera_x86_64_cpu_is_ready(0) || !to->kernel_stack_top ||
        (to->kernel_stack_top & 0xFu) != 0 || !canonical(to->kernel_stack_top)) return -1;
    uint64_t flags = 0;
    __asm__ volatile("pushfq; pop %0; cli" : "=r"(flags) :: "memory");
    const uint64_t root = koronos_address_space_current_root();
    if (!root || to->cr3 != root) {
        __asm__ volatile("push %0; popfq" :: "r"(flags) : "memory", "cc");
        return -2;
    }
    const uint64_t old_top = chimera_x86_64_cpu_kernel_stack(0);
    const uint32_t old_pid = chimera_x86_64_cpu_current_pid(0);
    const uint64_t bootstrap_top = chimera_x86_64_cpu_bootstrap_kernel_stack(0);
    bool valid = to->kernel_stack_top == bootstrap_top;
    if (!valid) {
        constexpr uint64_t page = 4096u;
        constexpr uint64_t bytes =
            static_cast<uint64_t>(KORONOS_KERNEL_STACK_USABLE_PAGES) * page;
        if (to->kernel_stack_top >= bytes + page) {
            const uint64_t base = to->kernel_stack_top - bytes;
            valid = to->rsp >= base && to->rsp < to->kernel_stack_top;
            for (uint32_t i = 0; valid && i < KORONOS_KERNEL_STACK_USABLE_PAGES; ++i)
                valid = koronos_address_space_kernel_page_mapped(
                    root, base + static_cast<uint64_t>(i) * page) == 1;
            if (valid) valid = koronos_address_space_kernel_page_mapped(root, base - page) == 0;
        }
    }
    if (!valid || !old_top) {
        __asm__ volatile("push %0; popfq" :: "r"(flags) : "memory", "cc");
        return -3;
    }
    from->cr3 = root;
    from->kernel_stack_top = old_top;
    from->pid = old_pid;
    if (chimera_x86_64_cpu_set_kernel_stack(0, to->kernel_stack_top) != 0 ||
        chimera_x86_64_cpu_set_current_pid(0, to->pid) != 0) {
        (void)chimera_x86_64_cpu_set_kernel_stack(0, old_top);
        (void)chimera_x86_64_cpu_set_current_pid(0, old_pid);
        __asm__ volatile("push %0; popfq" :: "r"(flags) : "memory", "cc");
        return -4;
    }
    const int result = koronos_x86_64_context_switch_raw(from, to);
    if (result != 0) {
        (void)chimera_x86_64_cpu_set_kernel_stack(0, old_top);
        (void)chimera_x86_64_cpu_set_current_pid(0, old_pid);
    }
    __asm__ volatile("push %0; popfq" :: "r"(flags) : "memory", "cc");
    return result;
}
