#include "chimera/process.h"
#include <stddef.h>
#if defined(KORONOS_PROCESS_RUNTIME_FREESTANDING)
#include "chimera/address_space.h"
#include "chimera/process_stack.h"
#endif

namespace {
constexpr uint32_t MAX_SEGMENTS = 16;
constexpr uint64_t PAGE = 4096;
constexpr uint64_t USER_MIN = 0x0000000100000000ull;
constexpr uint64_t USER_LIMIT = 0x0000800000000000ull;
constexpr uint32_t PT_LOAD = 1, PF_W = 2, PF_X = 1;

static void copy_bytes(void *destination, const void *source, uint64_t length) {
    auto *dst = static_cast<uint8_t *>(destination);
    const auto *src = static_cast<const uint8_t *>(source);
    for (uint64_t i = 0; i < length; ++i) dst[i] = src[i];
}
static bool add_ok(uint64_t a, uint64_t b, uint64_t *out) {
    if (a > UINT64_MAX - b) return false;
    *out = a + b;
    return true;
}
static uint64_t down(uint64_t x) { return x & ~(PAGE - 1); }
static bool up(uint64_t x, uint64_t *out) {
    if (x > UINT64_MAX - (PAGE - 1)) return false;
    *out = (x + PAGE - 1) & ~(PAGE - 1);
    return true;
}
static bool in(uint64_t offset, uint64_t length, uint64_t size) {
    uint64_t end = 0;
    return add_ok(offset, length, &end) && end <= size;
}

struct Slot {
    chimera_process_image image{};
    chimera_loaded_elf loaded{};
    chimera_elf_load_ops load_ops{};
    void *load_context = nullptr;
    koronos_kernel_stack kernel_stack{};
    bool has_kernel_stack = false;
    bool loaded_ok = false;
    bool execution_context_ready = false;
    bool used = false;
};
Slot slots[CHIMERA_PROCESS_MAX];
uint32_t next_pid = 1, count = 0;

static bool pid_in_use(uint32_t pid) {
    if (!pid) return true;
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i)
        if (slots[i].used && slots[i].image.pid == pid) return true;
    return false;
}
static uint32_t allocate_pid() {
    for (uint32_t attempt = 0; attempt < CHIMERA_PROCESS_MAX + 1u; ++attempt) {
        if (!next_pid || next_pid > 0x7fffffffu) next_pid = 1;
        const uint32_t candidate = next_pid++;
        if (candidate && !pid_in_use(candidate)) return candidate;
    }
    return 0;
}
static Slot *find_slot(uint32_t pid) {
    if (!pid) return nullptr;
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i)
        if (slots[i].used && slots[i].image.pid == pid) return &slots[i];
    return nullptr;
}
static bool destroy_loaded(Slot *slot) {
    if (!slot || !slot->loaded_ok) return true;
    if (slot->image.address_space == slot->loaded.address_space &&
        chimera_process_clear_address_space(slot->image.pid,
                                            slot->loaded.address_space) != 0)
        return false;
    if (slot->load_ops.destroy_address_space)
        slot->load_ops.destroy_address_space(slot->load_context,
                                             slot->loaded.address_space);
    slot->loaded = {};
    slot->load_ops = {};
    slot->load_context = nullptr;
    slot->loaded_ok = false;
    slot->execution_context_ready = false;
    slot->image.saved_rsp = 0;
    slot->image.saved_rip = 0;
    return true;
}
}

extern "C" int chimera_process_init(void) {
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i) slots[i] = {};
    next_pid = 1;
    count = 0;
    return 0;
}

extern "C" int chimera_process_admit_elf(const void *image, uint64_t size,
                                          uint16_t machine, uint64_t stack,
                                          chimera_process_image *out) {
    if (!image || !out || stack <= USER_MIN || stack >= USER_LIMIT ||
        (stack & (PAGE - 1))) return -1;
    if (!koronos_elf64_validate(image, size, machine)) return -2;

    koronos_elf64_ehdr h{};
    copy_bytes(&h, image, sizeof(h));
    if (h.e_type != KORONOS_ET_EXEC || h.e_phnum == 0 ||
        h.e_phnum > 4096u) return -2;

    const auto *bytes = static_cast<const uint8_t *>(image);
    chimera_process_image p{};
    p.entry = h.e_entry;
    p.user_stack_top = down(stack);
    uint32_t n = 0;
    uint64_t low = UINT64_MAX, high = 0;
    bool entry_executable = false;

    for (uint16_t i = 0; i < h.e_phnum; ++i) {
        koronos_elf64_phdr segment{};
        const uint64_t offset = h.e_phoff +
            static_cast<uint64_t>(i) * sizeof(koronos_elf64_phdr);
        copy_bytes(&segment, bytes + offset, sizeof(segment));
        if (segment.p_type != PT_LOAD) continue;
        if (segment.p_memsz < segment.p_filesz ||
            !in(segment.p_offset, segment.p_filesz, size)) return -3;

        uint64_t end = 0;
        if (!add_ok(segment.p_vaddr, segment.p_memsz, &end) ||
            segment.p_memsz == 0 || segment.p_vaddr < USER_MIN ||
            segment.p_vaddr >= USER_LIMIT || end > stack || end > USER_LIMIT)
            return -4;
        if (segment.p_align > 1 &&
            ((segment.p_align & (segment.p_align - 1)) != 0 ||
             (segment.p_vaddr % segment.p_align) !=
                 (segment.p_offset % segment.p_align))) return -5;
        if (n >= MAX_SEGMENTS) return -6;
        if ((segment.p_flags & (PF_W | PF_X)) == (PF_W | PF_X)) return -7;

        auto &destination = p.segments[n++];
        destination.file_offset = segment.p_offset;
        destination.virtual_address = down(segment.p_vaddr);
        destination.file_size = segment.p_filesz;
        destination.memory_size = end - destination.virtual_address;
        destination.flags = segment.p_flags;
        destination.align = segment.p_align ? segment.p_align : PAGE;
        if (destination.virtual_address < low) low = destination.virtual_address;

        uint64_t aligned_end = 0;
        if (!up(end, &aligned_end)) return -8;
        for (uint32_t j = 0; j + 1u < n; ++j) {
            uint64_t prior_end = 0;
            if (!add_ok(p.segments[j].virtual_address,
                        p.segments[j].memory_size, &prior_end) ||
                !up(prior_end, &prior_end)) return -8;
            if (destination.virtual_address < prior_end &&
                p.segments[j].virtual_address < aligned_end) return -11;
        }
        if (aligned_end > high) high = aligned_end;
        if ((segment.p_flags & PF_X) && h.e_entry >= segment.p_vaddr &&
            h.e_entry < end) entry_executable = true;
    }

    if (!n || p.entry < low || p.entry >= high || p.entry >= stack ||
        !entry_executable) return -9;
    p.segment_count = n;
    p.image_low = low;
    p.image_high = high;

    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i) {
        if (!slots[i].used) {
            p.pid = allocate_pid();
            if (!p.pid) return -10;
            p.state = CHIMERA_PROCESS_ADMITTED;
            slots[i].image = p;
            slots[i].used = true;
            ++count;
            *out = p;
            return static_cast<int>(p.pid);
        }
    }
    return -10;
}

extern "C" int chimera_process_bind_address_space(uint32_t pid, void *address_space,
                                                    uint64_t root, uint64_t entry,
                                                    uint64_t stack) {
    if (!address_space || !root || (root & (PAGE - 1)) ||
        entry < USER_MIN || entry >= USER_LIMIT ||
        stack < USER_MIN || stack >= USER_LIMIT) return -1;
#if defined(KORONOS_PROCESS_RUNTIME_FREESTANDING)
    if (root >= 0x100000000ull) return -1;
#else
    if (root >= USER_LIMIT) return -1;
#endif
    Slot *slot = find_slot(pid);
    if (!slot) return -2;
    if (slot->image.state != CHIMERA_PROCESS_ADMITTED ||
        slot->image.address_space || slot->image.address_space_root) return -3;
    if (entry != slot->image.entry || stack != slot->image.user_stack_top) return -4;
    slot->image.address_space = address_space;
    slot->image.address_space_root = root;
    slot->image.runtime_entry = entry;
    slot->image.runtime_stack = stack;
    return 0;
}

extern "C" int chimera_process_clear_address_space(uint32_t pid, void *expected) {
    Slot *slot = find_slot(pid);
    if (!slot) return -1;
    if (slot->image.state == CHIMERA_PROCESS_RUNNING) return -2;
    if (!expected || slot->image.address_space != expected) return -3;
    slot->image.address_space = nullptr;
    slot->image.address_space_root = 0;
    slot->image.runtime_entry = 0;
    slot->image.runtime_stack = 0;
    return 0;
}

extern "C" int chimera_process_load_elf(uint32_t pid, const void *image,
                                         uint64_t image_size, uint16_t machine,
                                         uint64_t stack_top, uint64_t stack_size,
                                         const chimera_elf_load_ops *ops,
                                         void *context) {
    Slot *slot = find_slot(pid);
    if (!slot || !image || !ops || slot->loaded_ok ||
        slot->image.state != CHIMERA_PROCESS_ADMITTED) return -1;
    chimera_loaded_elf loaded{};
    const int rc = chimera_elf_load_user_image(image, image_size, machine,
                                               stack_top, stack_size, ops,
                                               context, &loaded);
    if (rc != 0) return rc;
    uint64_t root = 0;
#if defined(KORONOS_PROCESS_RUNTIME_FREESTANDING)
    root = koronos_address_space_root(loaded.address_space);
#else
    root = reinterpret_cast<uint64_t>(loaded.address_space);
#endif
    if (!root || chimera_process_bind_address_space(
            pid, loaded.address_space, root, loaded.entry,
            loaded.user_stack_top) != 0) {
        ops->destroy_address_space(context, loaded.address_space);
        return -20;
    }
    slot->loaded = loaded;
    slot->load_ops = *ops;
    slot->load_context = context;
    slot->loaded_ok = true;
#if defined(KORONOS_PROCESS_RUNTIME_FREESTANDING)
    if (chimera_process_create_kernel_stack(pid) != 0) {
        (void)destroy_loaded(slot);
        return -21;
    }
#endif
    /* Address-space and kernel-stack ownership are real; the process remains
       ADMITTED until a validated user register frame and IRETQ path exist. */
    return 0;
}

extern "C" int chimera_process_release(uint32_t pid) {
    Slot *slot = find_slot(pid);
    if (!slot) return -1;
    if (slot->image.state != CHIMERA_PROCESS_ADMITTED &&
        slot->image.state != CHIMERA_PROCESS_EXITED &&
        slot->image.state != CHIMERA_PROCESS_FAULTED) return -2;
    if (!slot->loaded_ok && slot->image.address_space) return -4;
#if defined(KORONOS_PROCESS_RUNTIME_FREESTANDING)
    if (slot->has_kernel_stack && chimera_process_release_kernel_stack(pid) != 0)
        return -3;
#endif
    if (!destroy_loaded(slot)) return -4;
    *slot = {};
    if (count) --count;
    return 0;
}

extern "C" int chimera_process_get(uint32_t pid, chimera_process_image *out) {
    if (!out || !pid) return -1;
    Slot *slot = find_slot(pid);
    if (!slot) return -2;
    *out = slot->image;
    return 0;
}

extern "C" int chimera_process_set_state(uint32_t pid, chimera_process_state state) {
    if (!pid || state < CHIMERA_PROCESS_ADMITTED ||
        state > CHIMERA_PROCESS_FAULTED) return -1;
    Slot *slot = find_slot(pid);
    if (!slot) return -2;
    if ((state == CHIMERA_PROCESS_READY || state == CHIMERA_PROCESS_RUNNING ||
         state == CHIMERA_PROCESS_BLOCKED) &&
        (!slot->loaded_ok || !slot->execution_context_ready)) return -3;
    if ((state == CHIMERA_PROCESS_EXITED || state == CHIMERA_PROCESS_FAULTED) &&
        slot->image.state != CHIMERA_PROCESS_ADMITTED) return -4;
    slot->image.state = state;
    return 0;
}

extern "C" int chimera_process_attach_kernel_stack(
    uint32_t pid, const koronos_kernel_stack *stack) {
    if (!pid || !stack || stack->slot >= KORONOS_KERNEL_STACK_SLOT_COUNT ||
        !stack->generation || !stack->base || stack->top <= stack->base ||
        (stack->base & 0xFu) || (stack->top & 0xFu)) return -1;
    Slot *slot = find_slot(pid);
    if (!slot) return -3;
    if (slot->has_kernel_stack) return -2;
    slot->kernel_stack = *stack;
    slot->has_kernel_stack = true;
    slot->image.kernel_stack_base = stack->base;
    slot->image.kernel_stack_top = stack->top;
    return 0;
}

extern "C" int chimera_process_get_kernel_stack(
    uint32_t pid, koronos_kernel_stack *out_stack) {
    if (!pid || !out_stack) return -1;
    Slot *slot = find_slot(pid);
    if (!slot) return -3;
    if (!slot->has_kernel_stack) return -2;
    *out_stack = slot->kernel_stack;
    return 0;
}

extern "C" int chimera_process_detach_kernel_stack(
    uint32_t pid, koronos_kernel_stack *out_stack) {
    if (!pid || !out_stack) return -1;
    Slot *slot = find_slot(pid);
    if (!slot) return -3;
    if (!slot->has_kernel_stack) return -2;
    *out_stack = slot->kernel_stack;
    slot->kernel_stack = {};
    slot->has_kernel_stack = false;
    slot->image.kernel_stack_base = 0;
    slot->image.kernel_stack_top = 0;
    return 0;
}

extern "C" uint32_t chimera_process_count(void) { return count; }
