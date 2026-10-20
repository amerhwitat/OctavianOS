#include <cstdio>
#include <cstring>
#include <vector>
#include "chimera/process.h"
struct TestElf { koronos_elf64_ehdr h; koronos_elf64_phdr p; uint8_t code[16]; };
static void put32(std::vector<uint8_t>&v,uint32_t n){char b[9];std::snprintf(b,sizeof(b),"%08x",n);v.insert(v.end(),b,b+8);}
static void pad(std::vector<uint8_t>&v){while(v.size()%4)v.push_back(0);}
static void add_entry(std::vector<uint8_t>&v,const char*name,const char*data){
 const char magic[]="070701";v.insert(v.end(),magic,magic+6);put32(v,1);put32(v,0100644);put32(v,0);put32(v,0);put32(v,1);put32(v,0);put32(v,std::strlen(data));put32(v,0);put32(v,0);put32(v,0);put32(v,0);put32(v,std::strlen(name)+1);put32(v,0);v.insert(v.end(),name,name+std::strlen(name));v.push_back(0);pad(v);v.insert(v.end(),data,data+std::strlen(data));pad(v);
}
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
 std::vector<uint8_t> bytes;add_entry(bytes,"etc/motd","hello");add_entry(bytes,"TRAILER!!!","");chimera_cpio_archive archive{};
 CHECK(chimera_cpio_validate(&archive,bytes.data(),bytes.size())==CHIMERA_CPIO_OK);
 int fd=chimera_process_open_readonly(child.pid,&archive,"/etc/motd");CHECK(fd==3);
 char buf[8]{};uint64_t n=0;CHECK(chimera_process_read(child.pid,fd,buf,2,&n)==0&&n==2&&std::memcmp(buf,"he",2)==0);
 CHECK(chimera_process_read(child.pid,fd,buf,4,&n)==0&&n==3&&std::memcmp(buf,"llo",3)==0);
 CHECK(chimera_process_close(child.pid,fd)==0);CHECK(chimera_process_read(child.pid,fd,buf,1,&n)==-9);
 fd=chimera_process_open_readonly(child.pid,&archive,"etc/motd");CHECK(fd==3);
 uint32_t code=0xFFFFFFFFu;
 CHECK(chimera_process_waitpid_poll(parent.pid,child.pid,&code)==-3);
 CHECK(chimera_process_exit(child.pid,42)==0);
 CHECK(chimera_process_read(child.pid,fd,buf,1,&n)==-9);
 CHECK(chimera_process_exit(child.pid,7)==-3);
 CHECK(chimera_process_waitpid_poll(parent.pid,child.pid,&code)==0&&code==42);
 CHECK(chimera_process_count()==1);
 CHECK(chimera_process_waitpid_poll(parent.pid,child.pid,&code)==-2);
 std::puts("Process lifecycle metadata tests: PASS");return 0;
}
