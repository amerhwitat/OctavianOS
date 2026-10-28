#include "../include/chimera/process.h"
namespace { constexpr uint32_t MAX_SEGMENTS=16; constexpr uint64_t PAGE=4096; constexpr uint32_t PT_LOAD=1,PF_W=2,PF_X=1; struct Descriptor { chimera_cpio_file file{}; uint64_t offset=0; bool used=false; }; struct Slot { chimera_process_image image{}; chimera_process_runtime runtime{}; Descriptor fds[16]{}; bool used=false; }; Slot slots[CHIMERA_PROCESS_MAX]; uint32_t next_pid=1,count=0; static bool add_ok(uint64_t a,uint64_t b,uint64_t*o){if(a>UINT64_MAX-b)return false;*o=a+b;return true;} static uint64_t down(uint64_t x){return x&~(PAGE-1);} static bool up(uint64_t x,uint64_t*o){if(x>UINT64_MAX-(PAGE-1))return false;*o=(x+PAGE-1)&~(PAGE-1);return true;} static bool in(uint64_t o,uint64_t n,uint64_t z){uint64_t e=0;return add_ok(o,n,&e)&&e<=z;} static bool pid_in_use(uint32_t pid){if(!pid)return true;for(uint32_t i=0;i<CHIMERA_PROCESS_MAX;i++)if(slots[i].used&&slots[i].image.pid==pid)return true;return false;} static uint32_t allocate_pid(){for(uint32_t n=0;n<CHIMERA_PROCESS_MAX+1u;n++){if(!next_pid||next_pid>0x7fffffffu)next_pid=1;const uint32_t candidate=next_pid++;if(candidate&&!pid_in_use(candidate))return candidate;}return 0;} }
extern "C" int chimera_process_init(void){for(uint32_t i=0;i<CHIMERA_PROCESS_MAX;i++)slots[i]={};next_pid=1;count=0;return 0;}
extern "C" int chimera_process_admit_elf(const void*image,uint64_t size,uint16_t machine,uint64_t stack,chimera_process_image*out){if(!image||!out||stack<PAGE)return -1;const auto*h=(const koronos_elf64_ehdr*)image;if(size<sizeof(koronos_elf64_ehdr))return -2;if(!koronos_elf64_valid(h))return -2;if(h->e_machine!=machine||h->e_type!=KORONOS_ET_EXEC)return -2;if(h->e_phentsize!=sizeof(koronos_elf64_phdr)||!h->e_phnum||h->e_phnum>4096u||h->e_phoff>size||(uint64_t)h->e_phnum*sizeof(koronos_elf64_phdr)>size-h->e_phoff)return -2;const auto*ph=(const koronos_elf64_phdr*)((const uint8_t*)image+h->e_phoff);chimera_process_image p{};p.entry=h->e_entry;p.user_stack_top=down(stack);uint32_t n=0;uint64_t low=UINT64_MAX,high=0;bool entry_executable=false;for(uint16_t i=0;i<h->e_phnum;i++){const auto&s=ph[i];if(s.p_type!=PT_LOAD)continue;if(s.p_memsz<s.p_filesz||!in(s.p_offset,s.p_filesz,size))return -3;uint64_t end=0;if(!add_ok(s.p_vaddr,s.p_memsz,&end)||s.p_memsz==0||s.p_vaddr>=stack||end>stack)return -4;if(s.p_align&&(s.p_align&(s.p_align-1)))return -5;if(n>=MAX_SEGMENTS)return -6;if((s.p_flags&(PF_W|PF_X))==(PF_W|PF_X))return -7;auto&d=p.segments[n++];d.file_offset=s.p_offset;d.virtual_address=down(s.p_vaddr);d.file_size=s.p_filesz;d.memory_size=s.p_memsz+(s.p_vaddr-d.virtual_address);d.flags=s.p_flags;d.align=s.p_align?s.p_align:PAGE;if(d.virtual_address<low)low=d.virtual_address;uint64_t ae=0;if(!up(end,&ae))return -8;if(ae>high)high=ae;if((s.p_flags&PF_X)&&h->e_entry>=s.p_vaddr&&h->e_entry<end)entry_executable=true;}if(!n||p.entry<low||p.entry>=high||!entry_executable)return -9;p.segment_count=n;p.image_low=low;p.image_high=high;for(uint32_t i=0;i<CHIMERA_PROCESS_MAX;i++)if(!slots[i].used){p.pid=allocate_pid();if(!p.pid)return -10;p.state=CHIMERA_PROCESS_ADMITTED;slots[i].image=p;slots[i].used=true;++count;*out=p;return (int)p.pid;}return -10;}
extern "C" int chimera_process_get(uint32_t pid,chimera_process_image*out){if(!out||!pid)return -1;for(uint32_t i=0;i<CHIMERA_PROCESS_MAX;i++)if(slots[i].used&&slots[i].image.pid==pid){*out=slots[i].image;return 0;}return -2;}
extern "C" int chimera_process_set_state(uint32_t pid,chimera_process_state state){if(!pid||state<CHIMERA_PROCESS_ADMITTED||state>CHIMERA_PROCESS_FAULTED)return -1;for(uint32_t i=0;i<CHIMERA_PROCESS_MAX;i++)if(slots[i].used&&slots[i].image.pid==pid){if(state==CHIMERA_PROCESS_RUNNING&&!slots[i].runtime.bound)return -3;if((state==CHIMERA_PROCESS_EXITED||state==CHIMERA_PROCESS_FAULTED)&&slots[i].runtime.bound)return -4;slots[i].image.state=state;if(state==CHIMERA_PROCESS_EXITED||state==CHIMERA_PROCESS_FAULTED){if(state==CHIMERA_PROCESS_FAULTED&&slots[i].image.exit_code==0)slots[i].image.exit_code=1;for(uint32_t d=0;d<16;d++)slots[i].fds[d]={};}return 0;}return -2;}
extern "C" uint32_t chimera_process_count(void){return count;}
extern "C" int chimera_process_bind_runtime(uint32_t pid, void *address_space,
                                                   uint64_t root, uint64_t entry,
                                                   uint64_t stack_top) {
    if (!pid || !address_space || !root || (root & (PAGE - 1)) ||
        entry < 0x0000000100000000ull || entry >= 0x0000800000000000ull ||
        stack_top < 0x0000000100000000ull || stack_top >= 0x0000800000000000ull ||
        (stack_top & 0xFu)) return -1;
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i) {
        Slot &slot = slots[i];
        if (!slot.used || slot.image.pid != pid) continue;
        if (slot.runtime.bound ||
            (slot.image.state != CHIMERA_PROCESS_ADMITTED &&
             slot.image.state != CHIMERA_PROCESS_READY) ||
            slot.image.entry != entry) return -2;
        bool executable = false;
        for (uint32_t j = 0; j < slot.image.segment_count; ++j) {
            const chimera_elf_load_segment &segment = slot.image.segments[j];
            uint64_t segment_end = 0;
            if ((segment.flags & PF_X) &&
                add_ok(segment.virtual_address, segment.memory_size, &segment_end) &&
                entry >= segment.virtual_address && entry < segment_end) {
                executable = true;
                break;
            }
        }
        if (!executable) return -3;
        slot.runtime = {address_space, root, entry, stack_top, 1u, 0u};
        return 0;
    }
    return -4;
}
extern "C" int chimera_process_get_runtime(uint32_t pid,chimera_process_runtime*out){
 if(!pid||!out){return -1;}
 for(uint32_t i=0;i<CHIMERA_PROCESS_MAX;i++){if(slots[i].used&&slots[i].image.pid==pid){*out=slots[i].runtime;return 0;}}return -2;
}
extern "C" int chimera_process_unbind_runtime(uint32_t pid){
 if(!pid){return -1;}
 for(uint32_t i=0;i<CHIMERA_PROCESS_MAX;i++){if(slots[i].used&&slots[i].image.pid==pid){slots[i].runtime={};return 0;}}return -2;
}

extern "C" int chimera_process_set_parent(uint32_t child_pid,uint32_t parent_pid){
 if(!child_pid||!parent_pid||child_pid==parent_pid)return -1;
 Slot*child=nullptr;bool parent=false;
 for(uint32_t i=0;i<CHIMERA_PROCESS_MAX;i++)if(slots[i].used){
  if(slots[i].image.pid==child_pid)child=&slots[i];
  if(slots[i].image.pid==parent_pid)parent=true;
 }
 if(!child||!parent)return -2;
 if(child->image.parent_pid||child->image.state==CHIMERA_PROCESS_EXITED||child->image.state==CHIMERA_PROCESS_FAULTED)return -3;
 child->image.parent_pid=parent_pid;return 0;
}
extern "C" int chimera_process_exit(uint32_t pid,uint32_t code){
 if(!pid)return -1;
 for(uint32_t i=0;i<CHIMERA_PROCESS_MAX;i++)if(slots[i].used&&slots[i].image.pid==pid){
  if(slots[i].runtime.bound){return -4;}
  if(slots[i].image.state==CHIMERA_PROCESS_EXITED||slots[i].image.state==CHIMERA_PROCESS_FAULTED){return -3;}
  slots[i].image.exit_code=code&0xFFu;slots[i].image.state=CHIMERA_PROCESS_EXITED;for(uint32_t d=0;d<16;d++)slots[i].fds[d]={};return 0;
 }
 return -2;
}
extern "C" int chimera_process_waitpid_poll(uint32_t parent,uint32_t child,uint32_t*code){
 if(!parent||!child||parent==child||!code)return -1;
 Slot*p=nullptr;Slot*c=nullptr;
 for(uint32_t i=0;i<CHIMERA_PROCESS_MAX;i++)if(slots[i].used){
  if(slots[i].image.pid==parent)p=&slots[i];
  if(slots[i].image.pid==child)c=&slots[i];
 }
 if(!p||!c||c->image.parent_pid!=parent)return -2;
 if(c->image.reaped)return -4;
 if(c->runtime.bound){return -5;}
 if(c->image.state!=CHIMERA_PROCESS_EXITED&&c->image.state!=CHIMERA_PROCESS_FAULTED){return -3;}
 *code=c->image.exit_code;c->image.reaped=1;for(uint32_t d=0;d<16;d++)c->fds[d]={};c->used=false;if(count)--count;return 0;
}

extern "C" int chimera_process_open_readonly(uint32_t pid,const chimera_cpio_archive*archive,const char*path){
 if(!pid||!archive||!path)return -1;
 for(uint32_t i=0;i<CHIMERA_PROCESS_MAX;i++)if(slots[i].used&&slots[i].image.pid==pid){
  chimera_cpio_file file{};int r=chimera_cpio_find(archive,path,&file);if(r!=CHIMERA_CPIO_OK)return r;
  for(uint32_t d=0;d<16;d++)if(!slots[i].fds[d].used){slots[i].fds[d].file=file;slots[i].fds[d].offset=0;slots[i].fds[d].used=true;return static_cast<int>(d+3u);}
  return -24;
 }
 return -2;
}
extern "C" int chimera_process_read(uint32_t pid,int fd,void*buffer,uint64_t capacity,uint64_t*read_count){
 if(!pid||fd<3||fd>=19||!read_count||(!buffer&&capacity))return -1;
 for(uint32_t i=0;i<CHIMERA_PROCESS_MAX;i++)if(slots[i].used&&slots[i].image.pid==pid){
  Descriptor&d=slots[i].fds[static_cast<uint32_t>(fd-3)];if(!d.used)return -9;
  if(d.offset>d.file.size){*read_count=0;return 0;}
  int r=chimera_cpio_read(&d.file,d.offset,buffer,capacity,read_count);
  if(r!=CHIMERA_CPIO_OK)return r;
  d.offset+=*read_count;return 0;
 }
 return -2;
}
extern "C" int chimera_process_close(uint32_t pid,int fd){
 if(!pid||fd<3||fd>=19)return -1;
 for(uint32_t i=0;i<CHIMERA_PROCESS_MAX;i++)if(slots[i].used&&slots[i].image.pid==pid){
  Descriptor&d=slots[i].fds[static_cast<uint32_t>(fd-3)];if(!d.used)return -9;d={};return 0;
 }
 return -2;
}

extern "C" int chimera_process_seek(uint32_t pid, int fd, int64_t offset,
                                    uint32_t whence, uint64_t *new_offset) {
    if (!pid || !new_offset || fd < 3 || fd >= 19 || whence > 2u) return -22;
    for (uint32_t i = 0; i < CHIMERA_PROCESS_MAX; ++i) {
        if (!slots[i].used || slots[i].image.pid != pid) continue;
        Descriptor &descriptor = slots[i].fds[static_cast<uint32_t>(fd - 3)];
        if (!descriptor.used) return -9;
        uint64_t base = 0;
        if (whence == 1u) base = descriptor.offset;
        else if (whence == 2u) base = descriptor.file.size;
        uint64_t result = 0;
        if (offset < 0) {
            const uint64_t magnitude = static_cast<uint64_t>(-(offset + 1)) + 1u;
            if (magnitude > base) return -22;
            result = base - magnitude;
        } else {
            const uint64_t delta = static_cast<uint64_t>(offset);
            if (base > UINT64_MAX - delta) return -22;
            result = base + delta;
        }
        if (result > static_cast<uint64_t>(INT64_MAX)) return -22;
        descriptor.offset = result;
        *new_offset = result;
        return 0;
    }
    return -3;
}
