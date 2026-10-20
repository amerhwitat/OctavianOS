#include <stdint.h>
#include <stddef.h>
#include "chimera/vfs_cpio.h"
namespace {
constexpr uint64_t HEADER=110;
constexpr uint32_t S_IFMT=0170000, S_IFREG=0100000, S_IFDIR=0040000;
struct Entry { const uint8_t *name,*data; uint64_t name_len,data_len,next; uint32_t mode; bool trailer; };
static bool add(uint64_t a,uint64_t b,uint64_t *o){if(!o||a>UINT64_MAX-b)return false;*o=a+b;return true;}
static bool align4(uint64_t n,uint64_t *o){uint64_t t;if(!add(n,3,&t))return false;*o=t&~uint64_t(3);return true;}
static int hex8(const uint8_t*p,uint32_t*out){uint32_t v=0;if(!p||!out)return -1;for(unsigned i=0;i<8;i++){uint8_t c=p[i];uint32_t d;if(c>='0'&&c<='9')d=c-'0';else if(c>='a'&&c<='f')d=c-'a'+10;else if(c>='A'&&c<='F')d=c-'A'+10;else return -1;v=(v<<4)|d;}*out=v;return 0;}
static bool eq(const uint8_t*a,uint64_t an,const uint8_t*b,uint64_t bn){if(an!=bn)return false;for(uint64_t i=0;i<an;i++)if(a[i]!=b[i])return false;return true;}
static bool normalize(const uint8_t*p,uint64_t n,uint64_t *start,uint64_t *len){
 if(!p||!n||n>CHIMERA_CPIO_MAX_NAME||!start||!len)return false;
 uint64_t a=0;if(p[0]=='/'){a=1;if(n==1||p[1]=='/')return false;}
 uint64_t z=n;if(z>a&&p[z-1]=='/')--z;if(z<=a)return false;
 uint64_t component=a;
 for(uint64_t i=a;i<=z;i++){
  if(i==z||p[i]=='/'){
   uint64_t l=i-component;if(!l)return false;
   if((l==1&&p[component]=='.')||(l==2&&p[component]=='.'&&p[component+1]=='.'))return false;
   component=i+1;
  }
 }
 *start=a;*len=z-a;return true;
}
static bool entry_at(const uint8_t*b,uint64_t size,uint64_t off,Entry*out){
 if(!b||!out||off>size||size-off<HEADER)return false;
 const uint8_t*h=b+off;
 if(!((h[0]=='0'&&h[1]=='7'&&h[2]=='0'&&h[3]=='7'&&h[4]=='0'&&h[5]=='1')))return false;
 uint32_t mode=0,filesize=0,namesize=0;
 if(hex8(h+14,&mode)||hex8(h+54,&filesize)||hex8(h+94,&namesize)||!namesize||namesize>CHIMERA_CPIO_MAX_NAME+1u)return false;
 uint64_t nameoff,aftername,dataoff,end,afterdata,next;
 if(!add(off,HEADER,&nameoff)||!add(nameoff,namesize,&aftername)||aftername>size)return false;
 const uint8_t*name=b+nameoff;
 if(name[namesize-1]!=0)return false;
 for(uint32_t i=0;i+1<namesize;i++)if(name[i]==0)return false;
 if(!align4(aftername,&dataoff)||dataoff>size||!add(dataoff,filesize,&end)||end>size||!align4(end,&afterdata)||afterdata>size)return false;
 if(!add(afterdata,0,&next))return false;
 const bool trailer=namesize==11&&eq(name,10,(const uint8_t*)"TRAILER!!!",10);
 if(!trailer){
  uint64_t s=0,l=0;if(!normalize(name,namesize-1,&s,&l))return false;
  uint32_t type=mode&S_IFMT;if(type!=S_IFREG&&type!=S_IFDIR)return false;
  if(type==S_IFDIR&&filesize!=0)return false;
 }
 out->name=name;out->name_len=namesize-1;out->data=b+dataoff;out->data_len=filesize;out->next=next;out->mode=mode;out->trailer=trailer;return true;
}
static bool same_path(const Entry&a,const Entry&b){
 uint64_t as=0,al=0,bs=0,bl=0;
 if(!normalize(a.name,a.name_len,&as,&al)||!normalize(b.name,b.name_len,&bs,&bl))return false;
 return eq(a.name+as,al,b.name+bs,bl);
}
}
extern "C" int chimera_cpio_validate(chimera_cpio_archive*a,const void*bytes,uint64_t size){
 if(!a)return CHIMERA_CPIO_INVALID;
 a->bytes=nullptr;a->size=0;a->validated=0;
 if(!bytes||size<HEADER)return CHIMERA_CPIO_INVALID;
 const uint8_t*b=static_cast<const uint8_t*>(bytes);uint64_t off=0;uint32_t count=0;bool trailer=false;
 while(off<size){
  Entry cur{};if(!entry_at(b,size,off,&cur))return CHIMERA_CPIO_INVALID;
  if(cur.trailer){off=cur.next;trailer=true;break;}
  if(++count>4096u)return CHIMERA_CPIO_INVALID;
  uint64_t prior=0;
  while(prior<off){
   Entry old{};if(!entry_at(b,size,prior,&old)||old.trailer)return CHIMERA_CPIO_INVALID;
   if(same_path(cur,old))return CHIMERA_CPIO_DUPLICATE;
   if(old.next<=prior)return CHIMERA_CPIO_INVALID;
   prior=old.next;
  }
  if(cur.next<=off)return CHIMERA_CPIO_INVALID;
  off=cur.next;
 }
 if(!trailer)return CHIMERA_CPIO_INVALID;
 for(uint64_t i=off;i<size;i++)if(b[i]!=0)return CHIMERA_CPIO_INVALID;
 a->bytes=b;a->size=size;a->validated=CHIMERA_CPIO_ABI;return CHIMERA_CPIO_OK;
}
extern "C" int chimera_cpio_find(const chimera_cpio_archive*a,const char*path,chimera_cpio_file*out){
 if(!a||a->validated!=CHIMERA_CPIO_ABI||!a->bytes||!path||!out)return CHIMERA_CPIO_INVALID;
 uint64_t n=0;while(path[n]&&n<=CHIMERA_CPIO_MAX_NAME)++n;if(!n||n>CHIMERA_CPIO_MAX_NAME)return CHIMERA_CPIO_INVALID;
 uint64_t ps=0,pl=0;if(!normalize(reinterpret_cast<const uint8_t*>(path),n,&ps,&pl))return CHIMERA_CPIO_INVALID;
 uint64_t off=0;while(off<a->size){Entry e{};if(!entry_at(a->bytes,a->size,off,&e))return CHIMERA_CPIO_INVALID;if(e.trailer)break;
  uint64_t es=0,el=0;if(!normalize(e.name,e.name_len,&es,&el))return CHIMERA_CPIO_INVALID;
  if(eq(e.name+es,el,reinterpret_cast<const uint8_t*>(path)+ps,pl)){
   if((e.mode&S_IFMT)!=S_IFREG)return CHIMERA_CPIO_NOT_REGULAR;
   out->data=e.data;out->size=e.data_len;out->mode=e.mode;return CHIMERA_CPIO_OK;
  }off=e.next;
 }
 return CHIMERA_CPIO_NOT_FOUND;
}
extern "C" int chimera_cpio_read(const chimera_cpio_file*f,uint64_t offset,void*buffer,uint64_t capacity,uint64_t*read_count){
 if(!f||!read_count||(!buffer&&capacity))return CHIMERA_CPIO_INVALID;
 *read_count=0;if(offset>f->size)return CHIMERA_CPIO_RANGE;
 uint64_t n=f->size-offset;if(n>capacity)n=capacity;
 if(n&&!f->data)return CHIMERA_CPIO_INVALID;
 uint8_t*d=static_cast<uint8_t*>(buffer);for(uint64_t i=0;i<n;i++)d[i]=f->data[offset+i];
 *read_count=n;return CHIMERA_CPIO_OK;
}


namespace {
static chimera_cpio_archive g_root_archive{};
static volatile uint32_t g_root_mounted = 0;
static volatile uint32_t g_mount_lock = 0;
static void mount_lock() { while (__sync_lock_test_and_set(&g_mount_lock, 1u)) {} }
static void mount_unlock() { __sync_lock_release(&g_mount_lock); }
}
extern "C" int chimera_vfs_mount_readonly(const void *bytes, uint64_t size) {
    chimera_cpio_archive candidate{};
    const int rc = chimera_cpio_validate(&candidate, bytes, size);
    if (rc != CHIMERA_CPIO_OK) return rc;
    mount_lock();
    if (g_root_mounted) {
        mount_unlock();
        return -2; // A root mount is immutable for the lifetime of this boot.
    }
    g_root_archive = candidate;
    __sync_synchronize();
    g_root_mounted = 1;
    mount_unlock();
    return 0;
}
extern "C" int chimera_vfs_is_mounted(void) {
    return __atomic_load_n(&g_root_mounted, __ATOMIC_ACQUIRE) ? 1 : 0;
}
extern "C" const chimera_cpio_archive *chimera_vfs_root_archive(void) {
    return chimera_vfs_is_mounted() ? &g_root_archive : nullptr;
}
