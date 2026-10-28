#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include "chimera/compat.h"
#include "chimera/syscall.h"
#include "chimera/process.h"
#include "chimera/vfs_cpio.h"

static uint32_t yielded = 0;
extern "C" void chimera_sched_yield(void) { ++yielded; }
extern "C" uint64_t chimera_timer_now(void) { return 123456u; }

/* The host test links syscall.cpp to exercise the native dispatcher. These
   target-launch hooks belong to the ring-3 dispatcher and are intentionally
   inert in this isolated test executable. */
extern "C" uint32_t koronos_target_active_pid(void) { return 0u; }
extern "C" uint32_t koronos_target_validate_syscall_context(uint64_t) { return 0u; }
extern "C" int64_t koronos_console_write_user(uint64_t, uint64_t) { return -CHIMERA_ENOSYS; }
extern "C" void koronos_target_log(const char *) {}
extern "C" int koronos_target_validate_user_range(uint64_t, uint64_t, uint32_t) { return -1; }
/* This test intentionally does not link the VFS/process implementations. Keep
   their isolated-test substitutes fail-closed and exercise integration in the
   full kernel/ISO workflow instead. */
extern "C" const chimera_cpio_archive *chimera_vfs_root_archive(void) { return nullptr; }
extern "C" int chimera_process_open_readonly(uint32_t, const chimera_cpio_archive *, const char *) { return -CHIMERA_ENOSYS; }
extern "C" int chimera_process_read(uint32_t, int, void *, uint64_t, uint64_t *) { return -CHIMERA_ENOSYS; }
extern "C" int chimera_process_close(uint32_t, int) { return -CHIMERA_ENOSYS; }
extern "C" int chimera_process_seek(uint32_t, int, int64_t, uint32_t, uint64_t *) { return -CHIMERA_ENOSYS; }

int main() {
    assert(chimera_compat_init(1u, 64u) == 0);
    assert(chimera_syscall_init() == 0);
    uint64_t rv = 0;
    uint64_t args[CHIMERA_SYSCALL_MAX_ARGS] = {};
    /* Never claim PID 1 until a scheduler/process identity binding exists. */
    assert(chimera_syscall_dispatch(CHM_ENTRY_NATIVE, 64, CHM_SYS_GETPID, args, &rv) == -1);
    assert(rv == (uint64_t)(-(int64_t)CHIMERA_ENOSYS));
    /* Exit cannot be a successful no-op; teardown must be wired first. */
    assert(chimera_syscall_dispatch(CHM_ENTRY_NATIVE, 64, CHM_SYS_EXIT, args, &rv) == -1);
    assert(rv == (uint64_t)(-(int64_t)CHIMERA_ENOSYS));
    assert(chimera_syscall_dispatch(CHM_ENTRY_NATIVE, 64, CHM_SYS_YIELD, args, &rv) == 0);
    assert(rv == 0 && yielded == 1);
    assert(chimera_syscall_dispatch(CHM_ENTRY_NATIVE, 64, CHM_SYS_TIME_TICKS, args, &rv) == 0);
    assert(rv == 123456u);
    assert(chimera_syscall_dispatch(CHM_ENTRY_NATIVE, 64, CHM_SYS_MMAP, args, &rv) == -1);
    assert(rv == (uint64_t)(-(int64_t)CHIMERA_ENOSYS));
    puts("syscall backend honesty regression tests: PASS");
    return 0;
}
