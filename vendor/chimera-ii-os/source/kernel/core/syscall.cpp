#include "chimera/syscall.h"
#include "chimera/user_entry.h"
#include "chimera/address_space.h"
#include "chimera/compat.h"
#include "chimera/scheduler.h"
#include "chimera/timer.h"
#include "chimera/vfs_cpio.h"
#include "chimera/process.h"

namespace {
static volatile uint32_t g_initialized = 0;
static volatile uint32_t g_dispatched = 0;
static volatile uint32_t g_translated = 0;
static volatile uint32_t g_rejected = 0;
static volatile uint32_t g_last_os = 0;
static volatile uint32_t g_last_entry = 0;
static volatile uint32_t g_last_number = 0;
static volatile uint32_t g_last_canonical = 0xFFFFFFFFu;

static uint64_t error_value() {
    return (uint64_t)(-(int64_t)CHIMERA_ENOSYS);
}
}

extern "C" int chimera_syscall_init(void) {
    g_initialized = 1;
    return 0;
}

extern "C" int chimera_syscall_dispatch(uint32_t entry, uint32_t bitness, uint32_t number,
                                         const uint64_t *args, uint64_t *return_value) {
    if (!return_value) return -1;
    ++g_dispatched;

    chimera_syscall_identity id{};
    if (chimera_compat_recognize_syscall(entry, bitness, number, &id) != 0) {
        ++g_rejected;
        *return_value = error_value();
        return -1;
    }

    g_last_os = id.os;
    g_last_entry = id.entry;
    g_last_number = id.number;
    g_last_canonical = id.canonical;

    if (id.canonical != 0xFFFFFFFFu) ++g_translated;

    switch (id.canonical) {
        case CHM_SYS_GETPID:
            /* This compatibility dispatcher has no active process context.
             * The native ring-3 path resolves GETPID from the kernel-owned
             * active process record. Fail closed here rather than invent PID 1. */
            ++g_rejected;
            *return_value = error_value();
            return -1;
        case CHM_SYS_YIELD:
            chimera_sched_yield();
            *return_value = 0;
            return 0;
        case CHM_SYS_TIME_TICKS:
            *return_value = chimera_timer_now();
            return 0;
        case CHM_SYS_EXIT:
        case CHM_SYS_EXIT_GROUP:
            /* No process identity/teardown is available in this compatibility
             * dispatcher. Only the native process-bound entry may exit a task. */
            (void)args;
            ++g_rejected;
            *return_value = error_value();
            return -1;
        default:
            ++g_rejected;
            *return_value = error_value();
            return -1;
    }
}

extern "C" int chimera_syscall_get_snapshot(chimera_syscall_snapshot *out) {
    if (!out) return -1;
    out->abi = CHIMERA_SYSCALL_ABI;
    out->initialized = g_initialized;
    out->dispatched = g_dispatched;
    out->translated = g_translated;
    out->rejected = g_rejected;
    out->last_os = g_last_os;
    out->last_entry = g_last_entry;
    out->last_number = g_last_number;
    out->last_canonical = g_last_canonical;
    return 0;
}

extern "C" {
volatile uint64_t koronos_user_exit_code = 0;
}
extern "C" uint32_t koronos_target_active_pid(void);
extern "C" uint32_t koronos_target_validate_syscall_context(uint64_t user_rip);
extern "C" int64_t koronos_console_write_user(uint64_t address, uint64_t length);
extern "C" void koronos_target_log(const char *message);
extern "C" int koronos_target_validate_user_range(uint64_t address, uint64_t length,
                                                    uint32_t write_access);

namespace {
constexpr uint64_t USER_COPY_LIMIT = 4096u;
static int copy_user_path(uint64_t address, char *out, uint64_t capacity) {
    if (!address || !out || capacity < 2u || capacity > USER_COPY_LIMIT) return -22;
    for (uint64_t i = 0; i < capacity; ++i) {
        if (address > UINT64_MAX - i ||
            koronos_target_validate_user_range(address + i, 1u, 0u) != 0) return -14;
        const char c = *reinterpret_cast<const char *>(static_cast<uintptr_t>(address + i));
        out[i] = c;
        if (!c) return i ? 0 : -22;
    }
    out[capacity - 1u] = 0;
    return -36; // ENAMETOOLONG
}
static void copy_to_user_validated(uint64_t address, const uint8_t *src, uint64_t length) {
    volatile uint8_t *dst = reinterpret_cast<volatile uint8_t *>(static_cast<uintptr_t>(address));
    for (uint64_t i = 0; i < length; ++i) dst[i] = src[i];
}
}

extern "C" uint64_t koronos_syscall_user_dispatch(const koronos_user_syscall_frame *frame) {
    if (!frame) return static_cast<uint64_t>(-22ll);
    /* Temporary acceptance diagnostics: distinguish a failed INT 0x80 return
     * from a native SYSCALL context/dispatch failure without manufacturing
     * any userspace readiness marker. */
    koronos_target_log("[SYSC] entered native user syscall dispatcher");
    /* SYSCALL does not preserve caller CS. It may serve the active process,
     * but it cannot produce the CPL3 acceptance acknowledgement. That proof
     * is emitted only by the DPL3 INT 0x80 gate after checking saved CS.RPL. */
    if (!koronos_target_validate_syscall_context(frame->rcx)) {
        koronos_target_log("[SYSC] rejected user syscall context (RIP/CR3/PID mismatch)");
        return static_cast<uint64_t>(-38ll);
    }
    koronos_target_log("[SYSC] accepted user syscall context");
    switch (frame->rax) {
        case CHM_SYS_GETPID: {
            /* PID comes from the active kernel-owned process record. Never
             * fabricate PID 1 when no target process is actually running. */
            const uint32_t pid = koronos_target_active_pid();
            return pid ? static_cast<uint64_t>(pid) : static_cast<uint64_t>(-38ll);
        }
        case CHM_SYS_YIELD:
            /* Do not report a successful yield while this path has no resumable
             * process context or scheduler-owned address-space switch. The
             * current scheduler can cooperatively step callbacks, but that is
             * not a process-context switch. Keep this operation explicitly
             * unavailable until the syscall frame can be suspended and resumed. */
            return static_cast<uint64_t>(-38ll); // ENOSYS
        case CHM_SYS_TIME_TICKS:
            return chimera_timer_now();
        case CHM_SYS_WRITE: {
            const uint64_t fd = frame->rdi;
            const uint64_t address = frame->rsi;
            const uint64_t length = frame->rdx;
            if (fd > 2u || length > USER_COPY_LIMIT) return static_cast<uint64_t>(-22ll);
            /* Validate every page before the console backend dereferences user memory. */
            if (length && koronos_target_validate_user_range(address, length, 0u) != 0)
                return static_cast<uint64_t>(-14ll); // EFAULT
            return static_cast<uint64_t>(koronos_console_write_user(address, length));
        }
        case CHM_SYS_OPEN: {
            /* This ABI currently exposes only O_RDONLY (flags=0, mode=0).
             * Never silently accept write/create/truncate flags on a RO VFS. */
            if (frame->rsi != 0u || frame->rdx != 0u)
                return static_cast<uint64_t>(-22ll);
            char path[USER_COPY_LIMIT];
            const int copy_rc = copy_user_path(frame->rdi, path, sizeof(path));
            if (copy_rc != 0) return static_cast<uint64_t>(static_cast<int64_t>(copy_rc));
            const uint32_t pid = koronos_target_active_pid();
            if (!pid) return static_cast<uint64_t>(-3ll);
            return static_cast<uint64_t>(static_cast<int64_t>(chimera_process_open_readonly(pid, chimera_vfs_root_archive(), path)));
        }
        case CHM_SYS_READ: {
            const uint64_t fd = frame->rdi;
            const uint64_t address = frame->rsi;
            const uint64_t length = frame->rdx;
            if (fd > INT32_MAX || length > USER_COPY_LIMIT) return static_cast<uint64_t>(-22ll);
            if (length && koronos_target_validate_user_range(address, length, 1u) != 0)
                return static_cast<uint64_t>(-14ll);
            uint8_t buffer[USER_COPY_LIMIT];
            uint64_t bytes_read = 0;
            const uint32_t pid = koronos_target_active_pid();
            if (!pid) return static_cast<uint64_t>(-3ll);
            const int read_rc = chimera_process_read(pid, static_cast<int>(fd), buffer, length, &bytes_read);
            if (read_rc != 0) return static_cast<uint64_t>(static_cast<int64_t>(read_rc));
            if (bytes_read > length) return static_cast<uint64_t>(-5ll);
            if (bytes_read) copy_to_user_validated(address, buffer, bytes_read);
            return bytes_read;
        }
        case CHM_SYS_CLOSE: {
            if (frame->rdi > INT32_MAX) return static_cast<uint64_t>(-9ll);
            const uint32_t pid = koronos_target_active_pid();
            if (!pid) return static_cast<uint64_t>(-3ll);
            return static_cast<uint64_t>(static_cast<int64_t>(
                chimera_process_close(pid, static_cast<int>(frame->rdi))));
        }
        case CHM_SYS_SEEK: {
            if (frame->rdi > INT32_MAX || frame->rdx > 2u)
                return static_cast<uint64_t>(-22ll);
            const uint32_t pid = koronos_target_active_pid();
            if (!pid) return static_cast<uint64_t>(-3ll);
            uint64_t new_offset = 0;
            const int rc = chimera_process_seek(pid, static_cast<int>(frame->rdi),
                static_cast<int64_t>(frame->rsi), static_cast<uint32_t>(frame->rdx),
                &new_offset);
            if (rc != 0) return static_cast<uint64_t>(static_cast<int64_t>(rc));
            return new_offset;
        }
        case CHM_SYS_EXIT:
        case CHM_SYS_EXIT_GROUP:
            koronos_user_exit_code = frame->rdi & 0xFFu;
            koronos_target_log("[SYSC] userspace exit syscall received");
            return KORONOS_USER_SYSCALL_EXIT_SENTINEL;
        case CHM_SYS_FORK:
        case CHM_SYS_EXECVE:
        case CHM_SYS_WAITPID:
            // ABI numbers are reserved, but these operations must remain
            // explicitly unavailable until resumable process contexts, safe
            // address-space ownership transfer, and exit/reap are integrated.
            // Returning ENOSYS is safer than creating a fake PID or task.
            return static_cast<uint64_t>(-38ll);
        default:
            return static_cast<uint64_t>(-38ll);
    }
}
