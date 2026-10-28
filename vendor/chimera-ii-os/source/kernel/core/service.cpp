#include "../include/chimera/service.h"

namespace {
struct service_state { const char* id; uint32_t state; };
static service_state g_states[64];
static uint32_t g_state_count=0;
static bool same(const char*a,const char*b){
    if(!a||!b)return false;
    while(*a&&*b&&*a==*b){++a;++b;}
    return *a==0&&*b==0;
}
static int find(const chimera_service_manifest*s,uint32_t n,const char*id){
    for(uint32_t i=0;i<n;++i)
        if(same(s[i].id,id))return (int)i;
    return -1;
}
}
extern "C" int chimera_service_validate(const chimera_service_manifest*s,uint32_t n){
    if(!s||!n)return -1;
    if(n>CHIMERA_SERVICE_MAX_UNITS)return -5;
    for(uint32_t i=0;i<n;++i){
        if(s[i].abi_version!=CHIMERA_SERVICE_ABI||!s[i].id||s[i].id[0]==0)return -2;
        if(s[i].state>CHM_SVC_RECOVERING||
           (s[i].restart!=CHM_RESTART_NEVER&&s[i].restart!=CHM_RESTART_FAILURE))return -2;
        /* A unit cannot depend on more distinct units than this manifest contains.
           Bound this before walking the caller-provided dependency array. */
        if(s[i].dependency_count>n)return -4;
        if(s[i].dependency_count && !s[i].dependencies)return -4;
        for(uint32_t j=i+1;j<n;++j)
            if(same(s[i].id,s[j].id))return -3;
        for(uint32_t d=0;d<s[i].dependency_count;++d)
            if(!s[i].dependencies[d]||s[i].dependencies[d][0]==0||
               find(s,n,s[i].dependencies[d])<0)return -4;
    }
    return 0;
}
extern "C" int chimera_service_resolve(const chimera_service_manifest*s,uint32_t n,chimera_service_plan*p){
    if(!p||!p->ordered_ids||p->capacity<n)return -1;
    int v=chimera_service_validate(s,n);
    if(v<0)return v;
    uint8_t done[64]={};
    if(n>64)return -5;
    p->count=0;
    while(p->count<n){
        bool progressed=false;
        for(uint32_t i=0;i<n;++i){
            if(done[i])continue;
            bool ready=true;
            for(uint32_t d=0;d<s[i].dependency_count;++d){
                int k=find(s,n,s[i].dependencies[d]);
                if(k<0||!done[(uint32_t)k]){ready=false;break;}
            }
            if(ready){
                done[i]=1;
                p->ordered_ids[p->count++]=s[i].id;
                progressed=true;
            }
        }
        if(!progressed)return -6;
    }
    return 0;
}
extern "C" int chimera_service_resolve_waves(const chimera_service_manifest*s,uint32_t n,chimera_service_waves*w){
    if(!w||!w->unit_ids||!w->offsets||n==0||n>CHIMERA_SERVICE_MAX_UNITS||
       w->capacity<n||w->offsets_capacity<n+1u)return -1;
    const int valid=chimera_service_validate(s,n);
    if(valid<0)return valid;
    uint8_t done[CHIMERA_SERVICE_MAX_UNITS]={};
    uint32_t completed=0, waves=0;
    w->offsets[0]=0;
    while(completed<n){
        uint32_t selected=0;
        for(uint32_t i=0;i<n;i++){
            if(done[i])continue;
            bool ready=true;
            for(uint32_t d=0;d<s[i].dependency_count;d++){
                const int dep=find(s,n,s[i].dependencies[d]);
                if(dep<0||!done[(uint32_t)dep]){ready=false;break;}
            }
            if(ready){w->unit_ids[completed+selected]=s[i].id;selected++;}
        }
        if(!selected)return -6; // cycle or impossible dependency graph
        /* Mark the entire wave only after selection, so peers remain concurrent. */
        for(uint32_t j=0;j<selected;j++){
            const char*id=w->unit_ids[completed+j];
            const int idx=find(s,n,id);
            if(idx<0||done[(uint32_t)idx])return -7;
            done[(uint32_t)idx]=1;
        }
        completed+=selected;
        w->offsets[++waves]=completed;
    }
    w->wave_count=waves;
    return 0;
}
extern "C" int chimera_service_set_state(const char*id,uint32_t state){
    if(!id)return -1;
    for(uint32_t i=0;i<g_state_count;++i){
        if(same(g_states[i].id,id)){
            g_states[i].state=state;
            return 0;
        }
    }
    if(g_state_count>=64)return -2;
    g_states[g_state_count++]={id,state};
    return 0;
}
extern "C" int chimera_service_transition(const char*id,uint32_t expected,uint32_t next){
    if(!id||expected>CHM_SVC_RECOVERING||next>CHM_SVC_RECOVERING)return -1;
    const uint32_t current=chimera_service_get_state(id);
    if(current!=expected)return -2;
    /* Only explicit, conservative state edges are accepted. */
    bool allowed=false;
    switch(current){
      case CHM_SVC_DECLARED: allowed=(next==CHM_SVC_BLOCKED||next==CHM_SVC_STARTING||next==CHM_SVC_FAILED);break;
      case CHM_SVC_BLOCKED: allowed=(next==CHM_SVC_STARTING||next==CHM_SVC_FAILED);break;
      case CHM_SVC_STARTING: allowed=(next==CHM_SVC_RUNNING||next==CHM_SVC_FAILED||next==CHM_SVC_BLOCKED);break;
      case CHM_SVC_RUNNING: allowed=(next==CHM_SVC_STOPPING||next==CHM_SVC_FAILED||next==CHM_SVC_RECOVERING);break;
      case CHM_SVC_STOPPING: allowed=(next==CHM_SVC_STOPPED||next==CHM_SVC_FAILED);break;
      case CHM_SVC_STOPPED: allowed=(next==CHM_SVC_STARTING||next==CHM_SVC_FAILED);break;
      case CHM_SVC_FAILED: allowed=(next==CHM_SVC_RECOVERING||next==CHM_SVC_STARTING);break;
      case CHM_SVC_RECOVERING: allowed=(next==CHM_SVC_STARTING||next==CHM_SVC_FAILED||next==CHM_SVC_STOPPED);break;
      default: break;
    }
    if(!allowed)return -3;
    return chimera_service_set_state(id,next);
}
extern "C" int chimera_service_all_healthy(const char*const*ids,uint32_t n){
    if(!ids||!n)return 0;
    for(uint32_t i=0;i<n;i++)if(!ids[i]||chimera_service_get_state(ids[i])!=CHM_SVC_RUNNING)return 0;
    return 1;
}
extern "C" uint32_t chimera_service_get_state(const char*id){
    for(uint32_t i=0;i<g_state_count;++i)
        if(same(g_states[i].id,id))return g_states[i].state;
    return CHM_SVC_DECLARED;
}
extern "C" void chimera_kore_bootstrap(void){
    // Registration is not service execution. Keep services blocked until
    // real schedulable backends and health checks exist.
    chimera_service_set_state("chimera.device",CHM_SVC_BLOCKED);
    chimera_service_set_state("chimera.storage",CHM_SVC_BLOCKED);
    chimera_service_set_state("chimera.security",CHM_SVC_BLOCKED);
    chimera_service_set_state("chimera.logging",CHM_SVC_BLOCKED);
    chimera_service_set_state("chimera.kore",CHM_SVC_BLOCKED);
}
