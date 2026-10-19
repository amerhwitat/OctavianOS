#include "../include/chimera/process.h"

namespace {
constexpr uint32_t MAX_SEGMENTS = 16;
constexpr uint64_t PAGE = 4096;
constexpr uint64_t USER_LIMIT = 0x0000800000000000ull;
constexpr uint32_t PT_LOAD = 1u;
constexpr uint32_t PF_X = 1u, PF_W = 2u, PF_R = 4u;
struct Slot { chimera_process_image image{}; bool used = false; };
Slot slots[CHIMERA_PROCESS_MAX];
uint32_t next_pid = 1, count = 0;

static bool add_ok(uint64_t a, uint64_t b, uint64_t *out) {
    if (a > UINT64_MAX - b) return false;
    *out = a + b;
    return true;
}
static bool align_up(uint64_t value, uint64_t *out) {
    if (value > UINT64_MAX - (PAGE - 1u)) return false;
    *out = (value + PAGE - 1u) & ~(PAGE - 1u);
    return true;
}
static uint64_t align_down(uint64_t value) { return value & ~(PAGE - 1u); }
static bool inside(uint64_t offset, uint64_t length, uint64_t total) {
    uint64_t end = 0;
    return add_ok(offset, length, &end) && end <= total;
}
static bool pid_in_use(uint32_t pid) {
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i)
        if (slots[i].used && slots[i].image.pid == pid) return true;
    return false;
}
static uint32_t allocate_pid() {
    // PID zero is reserved. Never reuse a live PID after uint32_t wraparound.
    for (uint32_t tries = 0; tries < UINT32_MAX - 1u; ++tries) {
        uint32_t candidate = next_pid++;
        if (next_pid == 0) next_pid = 1;
        if (candidate != 0 && !pid_in_use(candidate)) return candidate;
    }
    return 0;
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
    if (!image || !out || stack < PAGE || stack >= USER_LIMIT) return -1;
    if (size < sizeof(koronos_elf64_ehdr)) return -2;

    koronos_elf64_ehdr h{};
    __builtin_memcpy(&h, image, sizeof(h));
    if (!koronos_elf64_valid(&h) || h.e_ehsize < sizeof(h) ||
        h.e_machine != machine || h.e_type != KORONOS_ET_EXEC ||
        h.e_phentsize != sizeof(koronos_elf64_phdr) || h.e_phnum == 0 ||
        h.e_phnum > MAX_SEGMENTS) return -2;

    const uint64_t ph_bytes = (uint64_t)h.e_phnum * h.e_phentsize;
    if (!inside(h.e_phoff, ph_bytes, size)) return -3;

    chimera_process_image p{};
    p.entry = h.e_entry;
    p.user_stack_top = align_down(stack);
    uint32_t n = 0;
    uint64_t low = UINT64_MAX, high = 0;
    bool entry_is_executable = false;
    const auto *bytes = static_cast<const uint8_t *>(image);

    for (uint16_t i = 0; i < h.e_phnum; ++i) {
        koronos_elf64_phdr s{};
        __builtin_memcpy(&s, bytes + h.e_phoff + (uint64_t)i * h.e_phentsize, sizeof(s));
        if (s.p_type != PT_LOAD) continue;
        if (n >= MAX_SEGMENTS || s.p_memsz == 0 || s.p_memsz < s.p_filesz ||
            !inside(s.p_offset, s.p_filesz, size) ||
            (s.p_flags & ~(PF_R | PF_W | PF_X)) != 0 ||
            (s.p_flags & (PF_W | PF_X)) == (PF_W | PF_X)) return -4;

        uint64_t end = 0, map_end = 0;
        if (!add_ok(s.p_vaddr, s.p_memsz, &end) ||
            s.p_vaddr >= USER_LIMIT || end > USER_LIMIT ||
            !align_up(end, &map_end) || map_end > USER_LIMIT) return -5;
        if (s.p_align > 1u &&
            ((s.p_align & (s.p_align - 1u)) != 0 ||
             (s.p_vaddr % s.p_align) != (s.p_offset % s.p_align))) return -6;

        auto &d = p.segments[n++];
        d.file_offset = s.p_offset;
        d.virtual_address = align_down(s.p_vaddr);
        d.file_size = s.p_filesz;
        d.memory_size = s.p_memsz + (s.p_vaddr - d.virtual_address);
        d.flags = s.p_flags;
        d.align = s.p_align ? s.p_align : PAGE;
        if (d.virtual_address < low) low = d.virtual_address;
        if (map_end > high) high = map_end;
        if ((s.p_flags & PF_X) && h.e_entry >= s.p_vaddr && h.e_entry < end)
            entry_is_executable = true;
    }

    if (!n || !entry_is_executable) return -7;
    const uint64_t stack_base = p.user_stack_top - PAGE;
    if (high > stack_base && low < p.user_stack_top) return -8;

    // Reject page-rounded segment overlap instead of silently combining permissions.
    for (uint32_t i = 0; i < n; ++i) {
        uint64_t seg_end = 0;
        if (!align_up(p.segments[i].virtual_address + p.segments[i].memory_size, &seg_end))
            return -9;
        for (uint32_t j = i + 1; j < n; ++j) {
            uint64_t other_end = 0;
            if (!align_up(p.segments[j].virtual_address + p.segments[j].memory_size, &other_end))
                return -9;
            if (p.segments[i].virtual_address < other_end &&
                p.segments[j].virtual_address < seg_end) return -10;
        }
    }

    if (count >= CHIMERA_PROCESS_MAX) return -11;
    uint32_t slot = CHIMERA_PROCESS_MAX;
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i)
        if (!slots[i].used) { slot = i; break; }
    if (slot == CHIMERA_PROCESS_MAX) return -11;

    const uint32_t pid = allocate_pid();
    if (!pid) return -12;
    p.pid = pid;
    p.state = CHIMERA_PROCESS_ADMITTED;
    p.segment_count = n;
    p.image_low = low;
    p.image_high = high;
    slots[slot].image = p;
    slots[slot].used = true;
    ++count;
    *out = p;
    return (int)pid;
}

extern "C" int chimera_process_get(uint32_t pid, chimera_process_image *out) {
    if (!out || !pid) return -1;
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i)
        if (slots[i].used && slots[i].image.pid == pid) {
            *out = slots[i].image;
            return 0;
        }
    return -2;
}

extern "C" int chimera_process_set_state(uint32_t pid, chimera_process_state state) {
    if (!pid || state < CHIMERA_PROCESS_ADMITTED || state > CHIMERA_PROCESS_FAULTED)
        return -1;
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i)
        if (slots[i].used && slots[i].image.pid == pid) {
            slots[i].image.state = state;
            return 0;
        }
    return -2;
}

extern "C" uint32_t chimera_process_count(void) { return count; }
