#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Called by the live/bootstrap scheduler task. Returns 0 only when no target
   ELF was selected or when the selected init exited after its own readiness
   handshake; negative values describe an explicit launch/acceptance failure. */
int koronos_launch_selected_userspace(void);
int koronos_target_note_user_write(const char *bytes, uint64_t length);
uint32_t koronos_target_userspace_ready(void);
/* Returns the kernel-owned PID only while a selected target process is active. */
uint32_t koronos_target_active_pid(void);
/* Acknowledges a syscall only when its saved user RIP and active CR3 match
   the currently launched process. Returns that process PID, otherwise zero. */
uint32_t koronos_target_note_user_syscall(uint64_t user_rip, uint64_t user_cs);
/* Context validation for SYSCALL, which does not save the caller CS. */
uint32_t koronos_target_validate_syscall_context(uint64_t user_rip);
/* Validates a range in the currently active process mapping. write_access is
   nonzero when the kernel will write into the user range. */
int koronos_target_validate_user_range(uint64_t address, uint64_t length,
                                       uint32_t write_access);

#ifdef __cplusplus
}
#endif
