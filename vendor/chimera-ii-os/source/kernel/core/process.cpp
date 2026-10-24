#include "../include/chimera/process.h"

namespace {
constexpr uint32_t MAX_SEGMENTS = 16;
constexpr uint64_t PAGE = 4096;
constexpr uint64_t USER_MIN = 0x0000000100000000ull;
constexpr uint64_t USER_LIMIT = 0x0000800000000000ull;
constexpr uint32_t PT_LOAD = 1u, PF_W = 2u, PF_X = 1u;
struct Slot { chimera_process_image image{}; bool used = false; };
Slot slots[CHIMERA_PROCESS_MAX];
uint32_t next_pid = 1, count = 0;

static bool add_ok(uint64_t a, uint64_t b, uint64_t *out) {
    if (a > UINT64_MAX - b) return false;
    *out = a + b;
    return true;
}
static uint64_t down(uint64_t x) { return x & ~(PAGE - 1u); }
static bool up(uint64_t x, uint64_t *out) {
    if (x > UINT64_MAX - (PAGE - 1u)) return false;
    *out = (x + PAGE - 1u) & ~(PAGE - 1u);
    return true;
}
static bool in(uint64_t offset, uint64_t length, uint64_t size) {
    uint64_t end = 0;
    return add_ok(offset, length, &end) && end <= size;
}
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
    if (!image || !out || size < sizeof(koronos_elf64_ehdr) || stack < USER_MIN ||
        stack >= USER_LIMIT) return -1;

    koronos_elf64_ehdr h{};
    __builtin_memcpy(&h, image, sizeof(h));
    if (!koronos_elf64_valid(&h) || h.e_version != 1u ||
        h.e_ehsize < sizeof(h) || h.e_type != KORONOS_ET_EXEC ||
        h.e_machine != machine || h.e_phentsize != sizeof(koronos_elf64_phdr) ||
        !h.e_phnum || h.e_phnum > 4096u) return -2;

    const uint64_t phbytes = static_cast<uint64_t>(h.e_phnum) * h.e_phentsize;
    if (!in(h.e_phoff, phbytes, size)) return -3;

    chimera_process_image p{};
    p.entry = h.e_entry;
    p.user_stack_top = down(stack);
    uint32_t n = 0;
    uint64_t low = UINT64_MAX, high = 0;
    bool entry_executable = false;
    const auto *bytes = static_cast<const uint8_t *>(image);

    for (uint16_t i = 0; i < h.e_phnum; ++i) {
        koronos_elf64_phdr s{};
        const uint64_t offset = h.e_phoff + static_cast<uint64_t>(i) * h.e_phentsize;
        __builtin_memcpy(&s, bytes + offset, sizeof(s));
        if (s.p_type != PT_LOAD) continue;
        if (s.p_memsz < s.p_filesz || !in(s.p_offset, s.p_filesz, size) ||
            !s.p_memsz || (s.p_flags & ~(PF_W | PF_X | 4u)) != 0u) return -4;

        uint64_t end = 0, aligned_end = 0;
        if (!add_ok(s.p_vaddr, s.p_memsz, &end) ||
            s.p_vaddr < USER_MIN || s.p_vaddr >= USER_LIMIT ||
            end > USER_LIMIT || end > p.user_stack_top ||
            !up(end, &aligned_end)) return -5;
        if (s.p_align > 1u &&
            ((s.p_align & (s.p_align - 1u)) != 0u ||
             (s.p_vaddr % s.p_align) != (s.p_offset % s.p_align))) return -6;
        if (n >= MAX_SEGMENTS) return -7;
        if ((s.p_flags & (PF_W | PF_X)) == (PF_W | PF_X)) return -8;

        auto &d = p.segments[n++];
        d.file_offset = s.p_offset;
        d.virtual_address = down(s.p_vaddr);
        d.file_size = s.p_filesz;
        d.memory_size = end - d.virtual_address;
        d.flags = s.p_flags;
        d.align = s.p_align ? s.p_align : PAGE;

        if (d.virtual_address < low) low = d.virtual_address;
        if (aligned_end > high) high = aligned_end;
        if ((s.p_flags & PF_X) && h.e_entry >= s.p_vaddr && h.e_entry < end)
            entry_executable = true;

        // Page-rounded segment overlaps require an explicit permission-merging
        // policy. Reject them before any mapper consumes this load plan.
        for (uint32_t j = 0; j + 1u < n; ++j) {
            uint64_t prior_end = 0;
            if (!add_ok(p.segments[j].virtual_address,
                        p.segments[j].memory_size, &prior_end) ||
                !up(prior_end, &prior_end)) return -9;
            if (d.virtual_address < prior_end &&
                p.segments[j].virtual_address < aligned_end) return -10;
        }
    }

    if (!n || !entry_executable || p.entry < low || p.entry >= high ||
        p.entry >= p.user_stack_top) return -11;

    // The initial stack is a separate mapping; never admit image pages that
    // overlap it, including after page rounding.
    const uint64_t stack_base = p.user_stack_top >= PAGE ? p.user_stack_top - PAGE : 0;
    for (uint32_t i = 0; i < n; ++i) {
        uint64_t segment_end = 0;
        if (!add_ok(p.segments[i].virtual_address, p.segments[i].memory_size,
                    &segment_end) || !up(segment_end, &segment_end)) return -12;
        if (p.segments[i].virtual_address < p.user_stack_top &&
            stack_base < segment_end) return -13;
    }

    p.segment_count = n;
    p.image_low = low;
    p.image_high = high;

    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i) {
        if (!slots[i].used) {
            p.pid = allocate_pid();
            if (!p.pid) return -14;
            p.state = CHIMERA_PROCESS_ADMITTED;
            slots[i].image = p;
            slots[i].used = true;
            ++count;
            *out = p;
            return static_cast<int>(p.pid);
        }
    }
    return -14;
}

extern "C" int chimera_process_get(uint32_t pid, chimera_process_image *out) {
    if (!out || !pid) return -1;
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i) {
        if (slots[i].used && slots[i].image.pid == pid) {
            *out = slots[i].image;
            return 0;
        }
    }
    return -2;
}

extern "C" int chimera_process_set_state(uint32_t pid, chimera_process_state state) {
    if (!pid || state < CHIMERA_PROCESS_ADMITTED ||
        state > CHIMERA_PROCESS_FAULTED) return -1;
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i) {
        if (slots[i].used && slots[i].image.pid == pid) {
            slots[i].image.state = state;
            return 0;
        }
    }
    return -2;
}

extern "C" int chimera_process_abort_start(uint32_t pid) {
    if (!pid) return -1;
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i) {
        if (!slots[i].used || slots[i].image.pid != pid) continue;
        // Only an admitted process that never entered READY/RUNNING can be
        // discarded here. Runtime exit/reap semantics are deliberately separate.
        if (slots[i].image.state != CHIMERA_PROCESS_ADMITTED) return -2;
        slots[i] = {};
        if (count) --count;
        return 0;
    }
    return -3;
}

extern "C" uint32_t chimera_process_count(void) { return count; }
