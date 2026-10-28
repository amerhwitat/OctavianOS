#include <cstdio>
#include <cstring>
#include "chimera/service.h"

static int check(bool ok,const char*what){if(!ok){std::fprintf(stderr,"FAIL: %s\n",what);return 1;}return 0;}
int main() {
    chimera_kore_bootstrap();
    const char *blocked_ids[] = {
        "chimera.device", "chimera.storage", "chimera.security",
        "chimera.logging", "chimera.kore"
    };
    for (const char *id : blocked_ids) {
        const uint32_t state = chimera_service_get_state(id);
        if (check(state == CHM_SVC_BLOCKED,"unbacked provider must remain BLOCKED")) return 1;
    }

    const char *ab_deps[]={"a"};
    const char *c_deps[]={"a"};
    const chimera_service_manifest units[] = {
        {CHIMERA_SERVICE_ABI,"a",CHM_SVC_DECLARED,CHM_RESTART_FAILURE,1,0,nullptr},
        {CHIMERA_SERVICE_ABI,"b",CHM_SVC_DECLARED,CHM_RESTART_FAILURE,0,0,nullptr},
        {CHIMERA_SERVICE_ABI,"c",CHM_SVC_DECLARED,CHM_RESTART_FAILURE,0,1,c_deps},
        {CHIMERA_SERVICE_ABI,"d",CHM_SVC_DECLARED,CHM_RESTART_NEVER,0,1,ab_deps}
    };
    const char *ids[4]{}; uint32_t offsets[5]{};
    chimera_service_waves waves{0,4,5,ids,offsets};
    if(check(chimera_service_resolve_waves(units,4,&waves)==0,"resolve parallel waves"))return 1;
    if(check(waves.wave_count==2,"two dependency waves expected"))return 1;
    if(check(offsets[0]==0&&offsets[1]==2&&offsets[2]==4,"independent a and b share first wave"))return 1;
    bool saw_a=false,saw_b=false,saw_c=false,saw_d=false;
    for(uint32_t i=offsets[0];i<offsets[1];i++){saw_a|=std::strcmp(ids[i],"a")==0;saw_b|=std::strcmp(ids[i],"b")==0;}
    for(uint32_t i=offsets[1];i<offsets[2];i++){saw_c|=std::strcmp(ids[i],"c")==0;saw_d|=std::strcmp(ids[i],"d")==0;}
    if(check(saw_a&&saw_b&&saw_c&&saw_d,"all units scheduled in dependency-safe waves"))return 1;

    const char *cycle_a[]={"y"}, *cycle_b[]={"x"};
    const chimera_service_manifest cycle[] = {
      {CHIMERA_SERVICE_ABI,"x",CHM_SVC_DECLARED,CHM_RESTART_NEVER,1,1,cycle_a},
      {CHIMERA_SERVICE_ABI,"y",CHM_SVC_DECLARED,CHM_RESTART_NEVER,1,1,cycle_b}
    };
    const char *cycle_ids[2]{}; uint32_t cycle_offsets[3]{};
    chimera_service_waves cycle_waves{0,2,3,cycle_ids,cycle_offsets};
    if(check(chimera_service_resolve_waves(cycle,2,&cycle_waves)==-6,"dependency cycle must fail closed"))return 1;

    if(check(chimera_service_transition("test.service",CHM_SVC_DECLARED,CHM_SVC_STARTING)==0,"declared to starting"))return 1;
    if(check(chimera_service_transition("test.service",CHM_SVC_STARTING,CHM_SVC_RUNNING)==0,"starting to running after health check"))return 1;
    const char *healthy[]={"test.service"};
    if(check(chimera_service_all_healthy(healthy,1)==1,"running service reports healthy"))return 1;
    if(check(chimera_service_transition("test.service",CHM_SVC_RUNNING,CHM_SVC_DECLARED)==-3,"invalid transition rejected"))return 1;
    std::puts("Service manager dependency-wave and health-state tests: PASS");
    return 0;
}
