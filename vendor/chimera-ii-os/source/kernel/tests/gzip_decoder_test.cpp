#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>
#include "chimera/gzip.h"
using Bytes=std::vector<uint8_t>;
static uint32_t crc32(const uint8_t *p,size_t n) {
    uint32_t c=0xffffffffu; for(size_t j=0;j<n;++j) { c^=p[j]; for(int i=0;i<8;++i)c=(c>>1)^((c&1)?0xedb88320u:0u); } return c^0xffffffffu;
}
static void le32(Bytes &b,uint32_t x){for(int i=0;i<4;++i)b.push_back((uint8_t)(x>>(8*i)));}
static Bytes stored_gzip(const char *s) {
    const size_t n=std::strlen(s); assert(n<65536);
    Bytes b={0x1f,0x8b,8,0,0,0,0,0,0,255,1,(uint8_t)n,(uint8_t)(n>>8),(uint8_t)~n,(uint8_t)(~n>>8)};
    b.insert(b.end(),s,s+n); le32(b,crc32(reinterpret_cast<const uint8_t*>(s),n)); le32(b,(uint32_t)n); return b;
}
static bool reject(Bytes b,uint64_t cap=128) {
    uint8_t out[128]; uint64_t n=99;
    return chimera_gzip_decompress_bounded(b.data(),b.size(),out,cap,&n)!=0 && n==0;
}
int main() {
    Bytes gz=stored_gzip("bounded gzip works");
    uint8_t out[128]={0}; uint64_t n=0;
    assert(chimera_gzip_decompress_bounded(gz.data(),gz.size(),out,sizeof(out),&n)==0);
    assert(n==18 && std::memcmp(out,"bounded gzip works",18)==0);
    assert(reject(gz,4));
    Bytes bad=gz; bad[bad.size()-8]^=1; assert(reject(bad));
    bad=gz; bad[3]=0xe0; assert(reject(bad));
    bad=gz; bad.pop_back(); assert(reject(bad));
    bad={0x1f,0x8b,8,0,0,0,0,0,0,255,7}; assert(reject(bad));
    std::puts("bounded gzip/DEFLATE tests: PASS");
}
