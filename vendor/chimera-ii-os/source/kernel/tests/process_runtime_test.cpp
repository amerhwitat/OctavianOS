#include "chimera/process.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>

struct Region {
    uint64_t base=0,size=0;
    uint32_t flags=0;
    uint8_t bytes[16384]{};
};
struct Mock {
    Region regions[4]{};
    uint32_t count=0;
    bool destroyed=false;
};
static void *create_as(void *opaque) {
    auto *mock=static_cast<Mock *>(opaque);
    mock->count=0; mock->destroyed=false;
    return mock;
}
static int map_pages(void *opaque,void *address_space,uint64_t base,
                     uint64_t size,uint32_t flags,void **alias) {
    auto *mock=static_cast<Mock *>(opaque);
    if(address_space!=opaque||!alias||mock->count>=4||
       size>sizeof(mock->regions[0].bytes)) return -1;
    for(uint32_t i=0;i<mock->count;i++)
        if(base<mock->regions[i].base+mock->regions[i].size&&
           mock->regions[i].base<base+size) return -2;
    auto &region=mock->regions[mock->count++];
    region.base=base; region.size=size; region.flags=flags;
    *alias=region.bytes;
    return 0;
}
static void destroy_as(void *opaque,void *address_space) {
    assert(opaque==address_space);
    static_cast<Mock *>(opaque)->destroyed=true;
}
static void put16(uint8_t *p,uint16_t v){p[0]=(uint8_t)v;p[1]=(uint8_t)(v>>8);}
static void put32(uint8_t *p,uint32_t v){for(int i=0;i<4;i++)p[i]=(uint8_t)(v>>(8*i));}
static void put64(uint8_t *p,uint64_t v){for(int i=0;i<8;i++)p[i]=(uint8_t)(v>>(8*i));}
static void build_elf(uint8_t *bytes,size_t size) {
    for(size_t i=0;i<size;i++) bytes[i]=0;
    bytes[0]=0x7f; bytes[1]='E'; bytes[2]='L'; bytes[3]='F';
    bytes[4]=2; bytes[5]=1; bytes[6]=1;
    put16(bytes+16,KORONOS_ET_EXEC);
    put16(bytes+18,KORONOS_EM_X86_64);
    put32(bytes+20,1);
    put64(bytes+24,0x100400100ull);
    put64(bytes+32,64);
    put16(bytes+52,64); put16(bytes+54,56); put16(bytes+56,1);
    put32(bytes+64,1); put32(bytes+68,5);
    put64(bytes+72,0x1000); put64(bytes+80,0x100400000ull);
    put64(bytes+96,16); put64(bytes+104,8192); put64(bytes+112,4096);
    for(int i=0;i<16;i++) bytes[0x1000+i]=0x90;
}
int main() {
    uint8_t image[8192]{};
    build_elf(image,sizeof(image));
    assert(chimera_process_init()==0);
    chimera_process_image admitted{};
    const int pid=chimera_process_admit_elf(
        image,sizeof(image),KORONOS_EM_X86_64,0x100800000ull,&admitted);
    assert(pid>0&&admitted.state==CHIMERA_PROCESS_ADMITTED);

    chimera_elf_load_ops ops{create_as,map_pages,destroy_as};
    alignas(4096) static Mock mock{};
    assert(chimera_process_load_elf((uint32_t)pid,image,sizeof(image),
        KORONOS_EM_X86_64,0x100800000ull,8192,&ops,&mock)==0);

    chimera_process_image runtime{};
    assert(chimera_process_get((uint32_t)pid,&runtime)==0);
    assert(runtime.address_space==&mock);
    assert(runtime.address_space_root==reinterpret_cast<uint64_t>(&mock));
    assert(runtime.runtime_entry==0x100400100ull);
    assert(runtime.runtime_stack==0x100800000ull);
    assert(runtime.kernel_stack_base==0&&runtime.kernel_stack_top==0);
    assert(runtime.saved_rsp==0&&runtime.saved_rip==0);
    assert(runtime.state==CHIMERA_PROCESS_ADMITTED);
    assert(chimera_process_set_state((uint32_t)pid,CHIMERA_PROCESS_READY)==-3);
    assert(chimera_process_release((uint32_t)pid)==0);
    assert(mock.destroyed&&chimera_process_count()==0);
    puts("Octavian process runtime: transactional address-space ownership, guarded-stack boundary, and not-runnable gate passed");
    return 0;
}
