#pragma once
#include <stdint.h>
#include "elf64.h"
#include "chimera/vfs_cpio.h"
#ifdef __cplusplus
extern "C" {
#endif
#define CHIMERA_PROCESS_ABI 2u
#define CHIMERA_PROCESS_MAX 128u
#define CHIMERA_PROCESS_LOAD_PLAN_ONLY 1u
typedef enum chimera_process_state { CHIMERA_PROCESS_EMPTY=0, CHIMERA_PROCESS_ADMITTED=1, CHIMERA_PROCESS_READY=2, CHIMERA_PROCESS_RUNNING=3, CHIMERA_PROCESS_BLOCKED=4, CHIMERA_PROCESS_EXITED=5, CHIMERA_PROCESS_FAULTED=6 } chimera_process_state;
typedef struct chimera_elf_load_segment { uint64_t file_offset,virtual_address,file_size,memory_size,flags,align; } chimera_elf_load_segment;
typedef struct chimera_process_image { uint32_t pid,state,segment_count,reserved; uint64_t entry,user_stack_top,image_low,image_high; chimera_elf_load_segment segments[16]; uint32_t parent_pid,exit_code,reaped,reserved2; } chimera_process_image;
typedef struct chimera_process_runtime { void *address_space; uint64_t root_physical,entry,user_stack_top; uint32_t bound,reserved; } chimera_process_runtime;
int chimera_process_init(void);
int chimera_process_admit_elf(const void*,uint64_t,uint16_t,uint64_t,chimera_process_image*);
int chimera_process_get(uint32_t,chimera_process_image*);
int chimera_process_bind_runtime(uint32_t,void*,uint64_t,uint64_t,uint64_t);
int chimera_process_get_runtime(uint32_t,chimera_process_runtime*);
int chimera_process_unbind_runtime(uint32_t);
int chimera_process_set_state(uint32_t,chimera_process_state);
uint32_t chimera_process_count(void);
/* Lifecycle metadata only: waitpid_poll is non-blocking and never claims scheduler sleep/wakeup. */
int chimera_process_set_parent(uint32_t child_pid,uint32_t parent_pid);
int chimera_process_exit(uint32_t pid,uint32_t exit_code);
int chimera_process_waitpid_poll(uint32_t parent_pid,uint32_t child_pid,uint32_t *exit_code);
/* Kernel-buffer helpers only; these are not user-pointer-safe syscall entry points. */
int chimera_process_open_readonly(uint32_t pid,const chimera_cpio_archive *archive,const char *path);
int chimera_process_read(uint32_t pid,int fd,void *kernel_buffer,uint64_t capacity,uint64_t *read_count);
int chimera_process_close(uint32_t pid,int fd);
int chimera_process_seek(uint32_t pid,int fd,int64_t offset,uint32_t whence,uint64_t *new_offset);
#ifdef __cplusplus
}
#endif
