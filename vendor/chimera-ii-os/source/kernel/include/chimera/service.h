#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define CHIMERA_SERVICE_ABI 0x00010000u
#define CHIMERA_SERVICE_MAX_UNITS 64u

enum chimera_service_state : uint32_t {
  CHM_SVC_DECLARED=0, CHM_SVC_BLOCKED=1, CHM_SVC_STARTING=2, CHM_SVC_RUNNING=3,
  CHM_SVC_STOPPING=4, CHM_SVC_STOPPED=5, CHM_SVC_FAILED=6, CHM_SVC_RECOVERING=7
};
enum chimera_service_restart : uint32_t { CHM_RESTART_NEVER=0, CHM_RESTART_FAILURE=1 };
struct chimera_service_manifest {
  uint32_t abi_version; const char* id; uint32_t state; uint32_t restart;
  uint8_t critical; uint8_t dependency_count; const char* const* dependencies;
};
/* Stable topological order for compatibility; dependencies are ordering edges. */
struct chimera_service_plan { uint32_t count; uint32_t capacity; const char** ordered_ids; };
/* Parallel-ready batches. offsets has wave_count+1 entries; ids are grouped by wave. */
struct chimera_service_waves {
  uint32_t wave_count;
  uint32_t capacity;
  uint32_t offsets_capacity;
  const char** unit_ids;
  uint32_t* offsets;
};
int chimera_service_validate(const chimera_service_manifest* services, uint32_t count);
int chimera_service_resolve(const chimera_service_manifest* services, uint32_t count, chimera_service_plan* plan);
int chimera_service_resolve_waves(const chimera_service_manifest* services, uint32_t count, chimera_service_waves* waves);
int chimera_service_set_state(const char* id, uint32_t state);
uint32_t chimera_service_get_state(const char* id);
int chimera_service_transition(const char* id, uint32_t expected_state, uint32_t next_state);
int chimera_service_all_healthy(const char* const* ids, uint32_t count);
void chimera_kore_bootstrap(void);
#ifdef __cplusplus
}
#endif
