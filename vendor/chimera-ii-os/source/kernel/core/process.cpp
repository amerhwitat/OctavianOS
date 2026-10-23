#include "../include/chimera/process.h"

namespace {
constexpr uint32_t MAX_SEGMENTS = 16;
constexpr uint64_t PAGE = 4096;
constexpr uint32_t PT_LOAD = 1, PF_W = 2, PF_X = 1;

struct Slot {
    chimera_process_image image{};
    uint32_t generation = 1;
    uint32_t parent_pid = 0;
    uint32_t parent_generation = 0;
    int32_t exit_status = 0;
    bool used = false;
    bool exited = false;
};
Slot slots[CHIMERA_PROCESS_MAX];
uint32_t next_pid = 1, count = 0;
uint32_t registry_lock = 0;
bool registry_initialized = false;

static void lock_registry() {
    while (__sync_lock_test_and_set(&registry_lock, 1u)) {}
}
static void unlock_registry() { __sync_lock_release(&registry_lock); }

static bool add_ok(uint64_t a, uint64_t b, uint64_t* out) {
    if (a > UINT64_MAX - b) return false;
    *out = a + b;
    return true;
}
static uint64_t down(uint64_t x) { return x & ~(PAGE - 1); }
static bool up(uint64_t x, uint64_t* out) {
    if (x > UINT64_MAX - (PAGE - 1)) return false;
    *out = (x + PAGE - 1) & ~(PAGE - 1);
    return true;
}
static bool in(uint64_t offset, uint64_t length, uint64_t size) {
    uint64_t end = 0;
    return add_ok(offset, length, &end) && end <= size;
}
static int find_pid_locked(uint32_t pid) {
    if (!pid) return -1;
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i)
        if (slots[i].used && slots[i].image.pid == pid) return (int)i;
    return -1;
}
static int find_handle_locked(chimera_process_handle h) {
    if (!h.pid || !h.generation) return -1;
    const int i = find_pid_locked(h.pid);
    if (i < 0 || slots[(uint32_t)i].generation != h.generation) return -1;
    return i;
}
static bool has_children_locked(chimera_process_handle parent) {
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i) {
        const Slot& child = slots[i];
        if (child.used && child.parent_pid == parent.pid &&
            child.parent_generation == parent.generation) return true;
    }
    return false;
}
static void clear_reaped_slot_locked(uint32_t i) {
    Slot& s = slots[i];
    s.used = false;
    s.exited = false;
    s.parent_pid = 0;
    s.parent_generation = 0;
    s.exit_status = 0;
    s.image = {};
    ++s.generation;
    if (s.generation == 0) s.generation = 1;
    if (count) --count;
}
}

extern "C" int chimera_process_init(void) {
    lock_registry();
    // Re-entry must not erase active process records or reset identity counters.
    if (registry_initialized) {
        unlock_registry();
        return 0;
    }
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i) slots[i] = {};
    next_pid = 1;
    count = 0;
    registry_initialized = true;
    unlock_registry();
    return 0;
}

extern "C" int chimera_process_admit_elf(const void* image, uint64_t size,
                                           uint16_t machine, uint64_t stack,
                                           chimera_process_image* out) {
    return chimera_process_admit_elf_child(image, size, machine, stack, nullptr, out, nullptr);
}

extern "C" int chimera_process_admit_elf_child(
    const void* image, uint64_t size, uint16_t machine, uint64_t stack,
    const chimera_process_handle* parent, chimera_process_image* out,
    chimera_process_handle* out_handle) {
    if (!image || !out || stack < PAGE || size < sizeof(koronos_elf64_ehdr)) return -1;
    const auto* h = static_cast<const koronos_elf64_ehdr*>(image);
    if (!koronos_elf64_valid(h) || h->e_machine != machine) return -2;
    uint64_t ph_bytes = 0, ph_end = 0;
    if (!h->e_phnum || h->e_phnum > 4096u ||
        h->e_phentsize != sizeof(koronos_elf64_phdr) ||
        !add_ok(0, static_cast<uint64_t>(h->e_phnum) * sizeof(koronos_elf64_phdr), &ph_bytes) ||
        !add_ok(h->e_phoff, ph_bytes, &ph_end) || ph_end > size) return -2;

    const auto* bytes = static_cast<const uint8_t*>(image);
    chimera_process_image p{};
    p.entry = h->e_entry;
    p.user_stack_top = down(stack);
    uint32_t n = 0;
    uint64_t low = UINT64_MAX, high = 0;
    bool entry_executable = false;

    for (uint16_t i = 0; i < h->e_phnum; ++i) {
        koronos_elf64_phdr s{};
        const uint64_t offset = h->e_phoff + static_cast<uint64_t>(i) * sizeof(s);
        const auto* src = reinterpret_cast<const uint8_t*>(&s);
        auto* dst = reinterpret_cast<uint8_t*>(&s);
        (void)src;
        for (uint64_t j = 0; j < sizeof(s); ++j) dst[j] = bytes[offset + j];
        if (s.p_type != PT_LOAD) continue;
        if (s.p_memsz < s.p_filesz || !in(s.p_offset, s.p_filesz, size)) return -3;
        uint64_t end = 0;
        if (!add_ok(s.p_vaddr, s.p_memsz, &end) || !s.p_memsz ||
            s.p_vaddr >= stack || end > stack) return -4;
        if (s.p_align > 1 && ((s.p_align & (s.p_align - 1)) ||
            (s.p_vaddr % s.p_align) != (s.p_offset % s.p_align))) return -5;
        if (n >= MAX_SEGMENTS || (s.p_flags & (PF_W | PF_X)) == (PF_W | PF_X)) return -6;
        auto& d = p.segments[n++];
        d.file_offset = s.p_offset;
        d.virtual_address = down(s.p_vaddr);
        d.file_size = s.p_filesz;
        d.memory_size = end - d.virtual_address;
        d.flags = s.p_flags;
        d.align = s.p_align ? s.p_align : PAGE;
        if (d.virtual_address < low) low = d.virtual_address;
        uint64_t aligned_end = 0;
        if (!up(end, &aligned_end)) return -7;
        if (aligned_end > high) high = aligned_end;
        if ((s.p_flags & PF_X) && h->e_entry >= s.p_vaddr && h->e_entry < end)
            entry_executable = true;
    }
    if (!n || !entry_executable) return -8;
    p.segment_count = n;
    p.image_low = low;
    p.image_high = high;

    lock_registry();
    if (!registry_initialized) {
        unlock_registry();
        return -9;
    }
    uint32_t parent_pid = 0, parent_generation = 0;
    if (parent) {
        const int parent_slot = find_handle_locked(*parent);
        if (parent_slot < 0 || slots[(uint32_t)parent_slot].exited) {
            unlock_registry();
            return -10;
        }
        parent_pid = parent->pid;
        parent_generation = parent->generation;
    }
    int free_slot = -1;
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i)
        if (!slots[i].used) { free_slot = (int)i; break; }
    if (free_slot < 0 || next_pid == 0 || next_pid > 0x7FFFFFFFu) {
        unlock_registry();
        return -11;
    }
    Slot& slot = slots[(uint32_t)free_slot];
    p.pid = next_pid++;
    p.state = CHIMERA_PROCESS_ADMITTED;
    slot.image = p;
    slot.parent_pid = parent_pid;
    slot.parent_generation = parent_generation;
    slot.exit_status = 0;
    slot.exited = false;
    slot.used = true;
    ++count;
    *out = p;
    if (out_handle) {
        out_handle->pid = p.pid;
        out_handle->generation = slot.generation;
    }
    const int result = static_cast<int>(p.pid);
    unlock_registry();
    return result;
}

extern "C" int chimera_process_get(uint32_t pid, chimera_process_image* out) {
    if (!out || !pid) return -1;
    lock_registry();
    const int i = find_pid_locked(pid);
    if (i < 0) { unlock_registry(); return -2; }
    *out = slots[(uint32_t)i].image;
    unlock_registry();
    return 0;
}

extern "C" int chimera_process_get_by_handle(chimera_process_handle handle,
                                               chimera_process_image* out) {
    if (!out) return -1;
    lock_registry();
    const int i = find_handle_locked(handle);
    if (i < 0) { unlock_registry(); return -2; }
    *out = slots[(uint32_t)i].image;
    unlock_registry();
    return 0;
}

extern "C" int chimera_process_set_state(uint32_t pid, chimera_process_state state) {
    // Terminal states must use chimera_process_exit() so wait/reap sees a
    // single exit transition and the corresponding status exactly once.
    if (!pid || state < CHIMERA_PROCESS_ADMITTED || state > CHIMERA_PROCESS_FAULTED ||
        state == CHIMERA_PROCESS_EXITED || state == CHIMERA_PROCESS_FAULTED)
        return -1;
    lock_registry();
    const int i = find_pid_locked(pid);
    if (i < 0 || slots[(uint32_t)i].exited) { unlock_registry(); return -2; }
    slots[(uint32_t)i].image.state = state;
    unlock_registry();
    return 0;
}

extern "C" int chimera_process_exit(chimera_process_handle handle, int32_t exit_status) {
    lock_registry();
    const int i = find_handle_locked(handle);
    if (i < 0) { unlock_registry(); return -1; }
    Slot& slot = slots[(uint32_t)i];
    if (slot.exited) { unlock_registry(); return -2; }
    slot.exited = true;
    slot.exit_status = exit_status;
    slot.image.state = CHIMERA_PROCESS_EXITED;
    unlock_registry();
    return 0;
}

extern "C" int chimera_process_fault(chimera_process_handle handle, int32_t fault_status) {
    lock_registry();
    const int i = find_handle_locked(handle);
    if (i < 0) { unlock_registry(); return -1; }
    Slot& slot = slots[(uint32_t)i];
    if (slot.exited) { unlock_registry(); return -2; }
    slot.exited = true;
    slot.exit_status = fault_status;
    slot.image.state = CHIMERA_PROCESS_FAULTED;
    unlock_registry();
    return 0;
}

extern "C" int chimera_process_wait_child(chimera_process_handle parent,
                                            chimera_process_handle* child_out,
                                            int32_t* status_out) {
    if (!child_out || !status_out) return -1;
    lock_registry();
    if (find_handle_locked(parent) < 0) { unlock_registry(); return -2; }
    bool found_child = false;
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i) {
        Slot& child = slots[i];
        if (!child.used || child.parent_pid != parent.pid ||
            child.parent_generation != parent.generation) continue;
        found_child = true;
        if (!child.exited) continue;
        // Preserve the ownership tree: an exited parent remains waitable until
        // its own children have been reaped, rather than orphaning live records.
        const chimera_process_handle child_handle{child.image.pid, child.generation};
        if (has_children_locked(child_handle)) {
            unlock_registry();
            return 0;
        }
        child_out->pid = child.image.pid;
        child_out->generation = child.generation;
        *status_out = child.exit_status;
        clear_reaped_slot_locked(i);
        unlock_registry();
        return 1;
    }
    unlock_registry();
    return found_child ? 0 : -3;
}

extern "C" uint32_t chimera_process_count(void) {
    lock_registry();
    const uint32_t n = count;
    unlock_registry();
    return n;
}
