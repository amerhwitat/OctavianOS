#include "../include/chimera/process.h"
namespace {
constexpr uint32_t MAX_SEGMENTS = 16;
constexpr uint64_t PAGE = 4096;
constexpr uint32_t PT_LOAD = 1, PF_W = 2, PF_X = 1;
constexpr uint64_t USER_LOW = 0x0000000100000000ull;
constexpr uint64_t USER_HIGH = 0x0000800000000000ull;

struct Slot {
    chimera_process_image image{};
    chimera_process_runtime runtime{};
    bool used = false;
};
Slot slots[CHIMERA_PROCESS_MAX];
uint32_t next_pid = 1, count = 0;

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
static void copy_bytes(void *destination, const void *source, uint64_t length) {
    auto *dst = static_cast<uint8_t *>(destination);
    const auto *src = static_cast<const uint8_t *>(source);
    for (uint64_t i = 0; i < length; ++i) dst[i] = src[i];
}
static bool pid_in_use(uint32_t pid) {
    if (!pid) return true;
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i)
        if (slots[i].used && slots[i].image.pid == pid) return true;
    return false;
}
/* Avoid wrapping PID allocation onto an existing live process record. */
static uint32_t allocate_pid() {
    for (uint32_t attempt = 0; attempt < CHIMERA_PROCESS_MAX + 1u; ++attempt) {
        if (!next_pid || next_pid > 0x7fffffffu) next_pid = 1;
        const uint32_t candidate = next_pid++;
        if (candidate && !pid_in_use(candidate)) return candidate;
    }
    return 0;
}
}
extern "C" int chimera_process_init(void){for(uint32_t i=0;i<CHIMERA_PROCESS_MAX;i++)slots[i]={};next_pid=1;count=0;return 0;}
extern "C" int chimera_process_bind_runtime(uint32_t pid,void* address_space,uint64_t root,uint64_t entry,uint64_t stack_top){
 if(!pid||!address_space||!root||(root&0xFFFu)||entry<0x0000000100000000ull||entry>=0x0000800000000000ull||
    stack_top<0x0000000100000000ull||stack_top>=0x0000800000000000ull||(stack_top&0xFu))return -1;
 for(uint32_t i=0;i<CHIMERA_PROCESS_MAX;i++){
  Slot&s=slots[i];if(!s.used||s.image.pid!=pid)continue;
  if(s.runtime.bound||(s.image.state!=CHIMERA_PROCESS_ADMITTED&&s.image.state!=CHIMERA_PROCESS_READY)||s.image.entry!=entry)return -2;
  bool executable=false;
  for(uint32_t j=0;j<s.image.segment_count;j++){
   const chimera_elf_load_segment&seg=s.image.segments[j];uint64_t end=0;
   if((seg.flags&PF_X)&&add_ok(seg.virtual_address,seg.memory_size,&end)&&entry>=seg.virtual_address&&entry<end){executable=true;break;}
  }
  if(!executable)return -3;
  s.runtime={address_space,root,entry,stack_top,1u,0u};return 0;
 }
 return -4;
}
extern "C" int chimera_process_get_runtime(uint32_t pid,chimera_process_runtime*out){
 if(!pid||!out)return -1;
 for(uint32_t i=0;i<CHIMERA_PROCESS_MAX;i++)if(slots[i].used&&slots[i].image.pid==pid){*out=slots[i].runtime;return 0;}
 return -2;
}
extern "C" int chimera_process_unbind_runtime(uint32_t pid){
 if(!pid)return -1;
 for(uint32_t i=0;i<CHIMERA_PROCESS_MAX;i++)if(slots[i].used&&slots[i].image.pid==pid){
  slots[i].runtime={};return 0;
 }
 return -2;
}

extern "C" int chimera_process_admit_elf(const void *image, uint64_t size,
                                          uint16_t machine, uint64_t stack,
                                          chimera_process_image *out) {
    if (!image || !out || stack < PAGE) return -1;
    if (size < sizeof(koronos_elf64_ehdr)) return -2;
    koronos_elf64_ehdr h{};
    copy_bytes(&h, image, sizeof(h));
    if (!koronos_elf64_valid(&h) || h.e_ehsize < sizeof(h) ||
        h.e_machine != machine || h.e_phentsize != sizeof(koronos_elf64_phdr) ||
        h.e_type != KORONOS_ET_EXEC || h.e_phnum == 0 ||
        h.e_phnum > 4096u) return -2;
    if (h.e_phoff > size) return -2;
    uint64_t phdr_bytes = 0, phdr_end = 0;
    if (!add_ok(static_cast<uint64_t>(h.e_phnum) * sizeof(koronos_elf64_phdr),
                0, &phdr_bytes) ||
        !add_ok(h.e_phoff, phdr_bytes, &phdr_end) || phdr_end > size)
        return -2;

    const auto *bytes = static_cast<const uint8_t *>(image);
    chimera_process_image p{};
    p.entry = h.e_entry;
    p.user_stack_top = down(stack);
    uint32_t n = 0;
    uint64_t low = UINT64_MAX, high = 0;
    bool entry_executable = false;

    for (uint16_t i = 0; i < h.e_phnum; ++i) {
        koronos_elf64_phdr seg{};
        const uint64_t offset = h.e_phoff +
            static_cast<uint64_t>(i) * sizeof(koronos_elf64_phdr);
        copy_bytes(&seg, bytes + offset, sizeof(seg));
        if (seg.p_type != PT_LOAD) continue;
        if (seg.p_memsz < seg.p_filesz ||
            !in(seg.p_offset, seg.p_filesz, size)) return -3;

        uint64_t end = 0;
        if (!add_ok(seg.p_vaddr, seg.p_memsz, &end) ||
            seg.p_memsz == 0 || seg.p_vaddr < USER_LOW ||
            seg.p_vaddr >= USER_HIGH || end > stack || end > USER_HIGH)
            return -4;
        if (seg.p_align > 1 &&
            ((seg.p_align & (seg.p_align - 1)) != 0 ||
             (seg.p_vaddr % seg.p_align) != (seg.p_offset % seg.p_align)))
            return -5;
        if (n >= MAX_SEGMENTS) return -6;
        if ((seg.p_flags & (PF_W | PF_X)) == (PF_W | PF_X)) return -7;

        auto &dst = p.segments[n++];
        dst.file_offset = seg.p_offset;
        dst.virtual_address = down(seg.p_vaddr);
        dst.file_size = seg.p_filesz;
        dst.memory_size = end - dst.virtual_address;
        dst.flags = seg.p_flags;
        dst.align = seg.p_align ? seg.p_align : PAGE;

        if (dst.virtual_address < low) low = dst.virtual_address;
        uint64_t aligned_end = 0;
        if (!up(end, &aligned_end)) return -8;
        /* Until the mapper can merge page permissions safely, reject PT_LOAD
         * segments whose page-rounded virtual ranges overlap. */
        for (uint32_t j = 0; j + 1u < n; ++j) {
            uint64_t prior_end = 0;
            if (!add_ok(p.segments[j].virtual_address,
                        p.segments[j].memory_size, &prior_end) ||
                !up(prior_end, &prior_end)) return -8;
            if (dst.virtual_address < prior_end &&
                p.segments[j].virtual_address < aligned_end) return -11;
        }
        if (aligned_end > high) high = aligned_end;
        if ((seg.p_flags & PF_X) && h.e_entry >= seg.p_vaddr &&
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
            slots[i].runtime = {};
            slots[i].used = true;
            ++count;
            *out = p;
            return static_cast<int>(p.pid);
        }
    }
    return -10;
}
extern "C" int chimera_process_get(uint32_t pid,chimera_process_image*out){if(!out||!pid)return -1;for(uint32_t i=0;i<CHIMERA_PROCESS_MAX;i++)if(slots[i].used&&slots[i].image.pid==pid){*out=slots[i].image;return 0;}return -2;}
extern "C" int chimera_process_set_state(uint32_t pid,chimera_process_state state){if(!pid||state<CHIMERA_PROCESS_ADMITTED||state>CHIMERA_PROCESS_FAULTED)return -1;for(uint32_t i=0;i<CHIMERA_PROCESS_MAX;i++)if(slots[i].used&&slots[i].image.pid==pid){if(state==CHIMERA_PROCESS_RUNNING&&!slots[i].runtime.bound)return -3;slots[i].image.state=state;return 0;}return -2;}
extern "C" uint32_t chimera_process_count(void){return count;}
