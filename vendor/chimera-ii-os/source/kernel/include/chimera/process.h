#pragma once
#include <stdint.h>
#include "elf64.h"
#ifdef __cplusplus
extern "C" {
#endif
#define CHIMERA_PROCESS_ABI 2u
#define CHIMERA_PROCESS_MAX 128u
#define CHIMERA_PROCESS_LOAD_PLAN_ONLY 1u
typedef enum chimera_process_state { CHIMERA_PROCESS_EMPTY=0, CHIMERA_PROCESS_ADMITTED=1, CHIMERA_PROCESS_READY=2, CHIMERA_PROCESS_RUNNING=3, CHIMERA_PROCESS_BLOCKED=4, CHIMERA_PROCESS_EXITED=5, CHIMERA_PROCESS_FAULTED=6 } chimera_process_state;
typedef struct chimera_elf_load_segment { uint64_t file_offset,virtual_address,file_size,memory_size,flags,align; } chimera_elf_load_segment;
typedef struct chimera_process_image { uint32_t pid,state,segment_count,reserved; uint64_t entry,user_stack_top,image_low,image_high; chimera_elf_load_segment segments[16]; uint32_t parent_pid,exit_code,reaped,reserved2; } chimera_process_image;
int chimera_process_init(void);
int chimera_process_admit_elf(const void*,uint64_t,uint16_t,uint64_t,chimera_process_image*);
int chimera_process_get(uint32_t,chimera_process_image*);
int chimera_process_set_state(uint32_t,chimera_process_state);
uint32_t chimera_process_count(void);
/* Lifecycle metadata only: waitpid_poll is non-blocking and never claims scheduler sleep/wakeup. */
int chimera_process_set_parent(uint32_t child_pid,uint32_t parent_pid);
int chimera_process_exit(uint32_t pid,uint32_t exit_code);
int chimera_process_waitpid_poll(uint32_t parent_pid,uint32_t child_pid,uint32_t *exit_code);
#ifdef __cplusplus
}
#endif
