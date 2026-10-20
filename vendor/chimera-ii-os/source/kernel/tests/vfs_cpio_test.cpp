#include <cstdio>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>
#include "chimera/vfs_cpio.h"
static void put32(std::vector<uint8_t>&v,uint32_t n){char b[9];std::snprintf(b,sizeof(b),"%08x",n);v.insert(v.end(),b,b+8);}
static void pad(std::vector<uint8_t>&v){while(v.size()%4)v.push_back(0);}
static void add(std::vector<uint8_t>&v,const char*name,const char*data,uint32_t mode=0100644){
 v.insert(v.end(),{'0','7','0','7','0','1'});put32(v,1);put32(v,mode);put32(v,0);put32(v,0);put32(v,1);put32(v,0);
 put32(v,static_cast<uint32_t>(std::strlen(data)));put32(v,0);put32(v,0);put32(v,0);put32(v,0);
 put32(v,static_cast<uint32_t>(std::strlen(name)+1));put32(v,0);v.insert(v.end(),name,name+std::strlen(name));v.push_back(0);pad(v);
 v.insert(v.end(),data,data+std::strlen(data));pad(v);
}
static std::vector<uint8_t> archive(const char*name,const char*data){std::vector<uint8_t>v;add(v,name,data);add(v,"TRAILER!!!","");return v;}
#define CHECK(x) do{if(!(x)){std::fprintf(stderr,"FAIL line %d: %s\n",__LINE__,#x);return 1;}}while(0)
int main(){
 auto v=archive("etc/motd","hello");chimera_cpio_archive a{};
 CHECK(chimera_cpio_validate(&a,v.data(),v.size())==CHIMERA_CPIO_OK);
 chimera_cpio_file f{};CHECK(chimera_cpio_find(&a,"/etc/motd",&f)==CHIMERA_CPIO_OK);
 char b[8]{};uint64_t got=0;CHECK(chimera_cpio_read(&f,1,b,3,&got)==CHIMERA_CPIO_OK);
 CHECK(got==3&&std::memcmp(b,"ell",3)==0);
 CHECK(chimera_cpio_read(&f,5,b,sizeof(b),&got)==CHIMERA_CPIO_OK&&got==0);
 CHECK(chimera_cpio_find(&a,"../etc/motd",&f)==CHIMERA_CPIO_INVALID);
 CHECK(chimera_cpio_find(&a,"etc/missing",&f)==CHIMERA_CPIO_NOT_FOUND);
 CHECK(chimera_cpio_validate(&a,v.data(),109)==CHIMERA_CPIO_INVALID);
 auto dup=archive("etc/motd","one");add(dup,"etc/motd","two");add(dup,"TRAILER!!!","");
 CHECK(chimera_cpio_validate(&a,dup.data(),dup.size())==CHIMERA_CPIO_DUPLICATE);
 auto traversal=archive("etc/../passwd","x");
 CHECK(chimera_cpio_validate(&a,traversal.data(),traversal.size())==CHIMERA_CPIO_INVALID);
 auto bad=archive("etc/x","y");bad[0]='X';CHECK(chimera_cpio_validate(&a,bad.data(),bad.size())==CHIMERA_CPIO_INVALID);
 auto missing=archive("etc/x","y");missing.resize(missing.size()-124);
 CHECK(chimera_cpio_validate(&a,missing.data(),missing.size())==CHIMERA_CPIO_INVALID);
 std::puts("CPIO VFS bounded parser tests: PASS");return 0;
}
