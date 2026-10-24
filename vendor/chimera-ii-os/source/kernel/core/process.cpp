#include "../include/chimera/process.h"

namespace {
constexpr uint32_t MAX_SEGMENTS = 16;
constexpr uint64_t PAGE = 4096;
constexpr uint32_t PT_LOAD = 1;
constexpr uint32_t PF_W = 2;
constexpr uint32_t PF_X = 1;

struct Slot {
    chimera_process_image image{};
    bool used = false;
};

Slot slots[CHIMERA_PROCESS_MAX];
uint32_t next_pid = 1;
uint32_t count = 0;

static bool add_ok(uint64_t a, uint64_t b, uint64_t *out) {
    if (!out || a > UINT64_MAX - b) return false;
    *out = a + b;
    return true;
}

static uint64_t down(uint64_t value) {
    return value & ~(PAGE - 1);
}

static bool up(uint64_t value, uint64_t *out) {
    if (!out || value > UINT64_MAX - (PAGE - 1)) return false;
    *out = (value + PAGE - 1) & ~(PAGE - 1);
    return true;
}

static bool in(uint64_t offset, uint64_t length, uint64_t size) {
    uint64_t end = 0;
    return add_ok(offset, length, &end) && end <= size;
}

static bool pid_in_use(uint32_t pid) {
    if (!pid) return true;
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i) {
        if (slots[i].used && slots[i].image.pid == pid) return true;
    }
    return false;
}

/* PID wraparound must never alias a live process record. */
static uint32_t allocate_pid() {
    for (uint32_t attempts = 0; attempts < CHIMERA_PROCESS_MAX + 1u; ++attempts) {
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
    if (!image || !out || stack < PAGE) return -1;
    if (size < sizeof(koronos_elf64_ehdr)) return -2;

    const auto *h = static_cast<const koronos_elf64_ehdr *>(image);
    if (!koronos_elf64_valid(h) || h->e_machine != machine) return -2;

    /* Validate the complete program-header table before forming/dereferencing
       the pointer. A malformed ELF must not cause an out-of-bounds kernel read. */
    if (h->e_phentsize != sizeof(koronos_elf64_phdr) || h->e_phnum == 0) return -2;
    uint64_t ph_bytes = 0;
    if (h->e_phnum > UINT64_MAX / sizeof(koronos_elf64_phdr)) return -2;
    ph_bytes = static_cast<uint64_t>(h->e_phnum) * sizeof(koronos_elf64_phdr);
    if (!in(h->e_phoff, ph_bytes, size)) return -2;

    const auto *bytes = static_cast<const uint8_t *>(image);
    const auto *ph = reinterpret_cast<const koronos_elf64_phdr *>(bytes + h->e_phoff);
    chimera_process_image plan{};
    plan.entry = h->e_entry;
    plan.user_stack_top = down(stack);

    uint32_t segment_count = 0;
    uint64_t low = UINT64_MAX;
    uint64_t high = 0;

    for (uint16_t i = 0; i < h->e_phnum; ++i) {
        const auto &s = ph[i];
        if (s.p_type != PT_LOAD) continue;
        if (s.p_memsz < s.p_filesz || !in(s.p_offset, s.p_filesz, size)) return -3;

        uint64_t end = 0;
        if (!add_ok(s.p_vaddr, s.p_memsz, &end) || s.p_memsz == 0 ||
            s.p_vaddr >= stack || end > stack) return -4;
        if (s.p_align && (s.p_align & (s.p_align - 1))) return -5;
        if (segment_count >= MAX_SEGMENTS) return -6;
        if ((s.p_flags & (PF_W | PF_X)) == (PF_W | PF_X)) return -7;

        auto &dest = plan.segments[segment_count++];
        dest.file_offset = s.p_offset;
        dest.virtual_address = down(s.p_vaddr);
        dest.file_size = s.p_filesz;
        if (!add_ok(s.p_memsz, s.p_vaddr - dest.virtual_address, &dest.memory_size)) return -8;
        dest.flags = s.p_flags;
        dest.align = s.p_align ? s.p_align : PAGE;

        if (dest.virtual_address < low) low = dest.virtual_address;
        uint64_t aligned_end = 0;
        if (!up(end, &aligned_end)) return -8;
        if (aligned_end > high) high = aligned_end;
    }

    if (!segment_count || plan.entry < low || plan.entry >= high) return -9;
    plan.segment_count = segment_count;
    plan.image_low = low;
    plan.image_high = high;

    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i) {
        if (slots[i].used) continue;
        const uint32_t pid = allocate_pid();
        if (!pid) return -10;
        plan.pid = pid;
        plan.state = CHIMERA_PROCESS_ADMITTED;
        slots[i].image = plan;
        slots[i].used = true;
        ++count;
        *out = plan;
        return static_cast<int>(pid);
    }
    return -10;
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
    if (!pid || state < CHIMERA_PROCESS_ADMITTED || state > CHIMERA_PROCESS_FAULTED) return -1;
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i) {
        if (slots[i].used && slots[i].image.pid == pid) {
            slots[i].image.state = state;
            return 0;
        }
    }
    return -2;
}

extern "C" uint32_t chimera_process_count(void) {
    return count;
}
