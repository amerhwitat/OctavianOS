#pragma once
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Called by the live/bootstrap scheduler task. An untargeted kernel-only smoke
   boot may return 0 without an init ELF. A selected Live/Installer/Recovery
   target without its native init ELF fails closed; successful launch returns 0
   only after the selected init reports readiness and exits cleanly. */
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

#ifdef __cplusplus
}
#endif
