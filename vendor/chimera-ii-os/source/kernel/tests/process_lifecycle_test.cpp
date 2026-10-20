#include <cstdio>
#include <cstring>
#include "chimera/process.h"
struct TestElf { koronos_elf64_ehdr h; koronos_elf64_phdr p; uint8_t code[16]; };
static int admit(chimera_process_image*out){
 TestElf image{};image.h.e_ident[0]=0x7f;image.h.e_ident[1]='E';image.h.e_ident[2]='L';image.h.e_ident[3]='F';
 image.h.e_ident[4]=KORONOS_ELFCLASS64;image.h.e_ident[5]=KORONOS_ELFDATA2LSB;
 image.h.e_type=KORONOS_ET_EXEC;image.h.e_machine=KORONOS_EM_X86_64;image.h.e_version=1;
 image.h.e_entry=0x400000;image.h.e_phoff=sizeof(koronos_elf64_ehdr);image.h.e_ehsize=sizeof(koronos_elf64_ehdr);
 image.h.e_phentsize=sizeof(koronos_elf64_phdr);image.h.e_phnum=1;
 image.p.p_type=1;image.p.p_flags=5;image.p.p_offset=sizeof(koronos_elf64_ehdr)+sizeof(koronos_elf64_phdr);
 image.p.p_vaddr=0x400000;image.p.p_filesz=sizeof(image.code);image.p.p_memsz=sizeof(image.code);image.p.p_align=4096;
 return chimera_process_admit_elf(&image,sizeof(image),KORONOS_EM_X86_64,0x800000,out);
}
#define CHECK(x) do{if(!(x)){std::fprintf(stderr,"FAIL line %d: %s\n",__LINE__,#x);return 1;}}while(0)
int main(){
 CHECK(chimera_process_init()==0);chimera_process_image parent{},child{};
 CHECK(admit(&parent)>0);CHECK(admit(&child)>0);CHECK(chimera_process_count()==2);
 CHECK(chimera_process_set_parent(child.pid,parent.pid)==0);
 uint32_t code=0xFFFFFFFFu;
 CHECK(chimera_process_waitpid_poll(parent.pid,child.pid,&code)==-3);
 CHECK(chimera_process_exit(child.pid,42)==0);
 CHECK(chimera_process_exit(child.pid,7)==-3);
 CHECK(chimera_process_waitpid_poll(parent.pid,child.pid,&code)==0&&code==42);
 CHECK(chimera_process_count()==1);
 CHECK(chimera_process_waitpid_poll(parent.pid,child.pid,&code)==-2);
 std::puts("Process lifecycle metadata tests: PASS");return 0;
}
