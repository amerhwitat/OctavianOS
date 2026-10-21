#include <stddef.h>
#include <stdint.h>

/* Production target init deliberately proves only the capabilities that exist.
 * It verifies CPL3 + process-owned GETPID and reads the target marker from the
 * mounted CPIO root, then exits blocked until real persistent services exist.
 * It must never emit USERSPACE READY merely because the probe ran. */
#if defined(CHIMERA_TARGET_LIVE)
#define TARGET_NAME "live"
#define TARGET_BYTES "live"
#elif defined(CHIMERA_TARGET_INSTALLER)
#define TARGET_NAME "installer"
#define TARGET_BYTES "installer"
#elif defined(CHIMERA_TARGET_RECOVERY)
#define TARGET_NAME "recovery"
#define TARGET_BYTES "recovery"
#else
#error "Select CHIMERA_TARGET_LIVE, CHIMERA_TARGET_INSTALLER, or CHIMERA_TARGET_RECOVERY"
#endif

static long syscall3(long n, long a, long b, long c) {
    register long rax __asm__("rax") = n;
    register long rdi __asm__("rdi") = a;
    register long rsi __asm__("rsi") = b;
    register long rdx __asm__("rdx") = c;
    __asm__ volatile("syscall"
                     : "+a"(rax)
                     : "D"(rdi), "S"(rsi), "d"(rdx)
                     : "rcx", "r11", "memory");
    return rax;
}

static size_t text_len(const char *s) {
    size_t n = 0;
    while (s[n]) ++n;
    return n;
}

static void write_text(const char *s) {
    (void)syscall3(9, 1, (long)s, (long)text_len(s)); /* CHM_SYS_WRITE */
}

static __attribute__((noreturn)) void exit_with(long code) {
    (void)syscall3(1, code, 0, 0); /* CHM_SYS_EXIT */
    for (;;) __asm__ volatile("pause" ::: "memory");
}

static int same_prefix(const char *got, const char *expected, size_t n) {
    for (size_t i = 0; i < n; ++i) if (got[i] != expected[i]) return 0;
    return 1;
}

static void write_pid(long pid) {
    char out[96];
    const char prefix[] = "NATIVE INIT PID: target=" TARGET_NAME " pid=";
    size_t used = 0;
    for (size_t i = 0; i < sizeof(prefix) - 1u; ++i) out[used++] = prefix[i];
    char digits[20];
    size_t count = 0;
    unsigned long value = (unsigned long)pid;
    do {
        digits[count++] = (char)('0' + (value % 10u));
        value /= 10u;
    } while (value && count < sizeof(digits));
    while (count) out[used++] = digits[--count];
    out[used++] = '\n';
    out[used] = '\0';
    write_text(out);
}

__attribute__((noreturn, used)) void _start(void) {
    /* The kernel separately acknowledges INT 0x80 only after validating CPL3. */
    __asm__ volatile("int $0x80" ::: "memory");
    const long pid = syscall3(2, 0, 0, 0); /* process-owned CHM_SYS_GETPID */
    if (pid <= 0) {
        write_text("NATIVE INIT ERROR: process-owned GETPID failed\n");
        exit_with(77);
    }
    write_pid(pid);

    static const char marker_path[] = "/etc/chimera/target";
    char marker[32] = {0};
    const long fd = syscall3(20, (long)marker_path, 0, 0); /* O_RDONLY */
    if (fd < 3) {
        write_text("NATIVE INIT ERROR: cannot OPEN target marker from mounted rootfs\n");
        exit_with(77);
    }
    const long bytes = syscall3(8, fd, (long)marker, (long)(sizeof(marker) - 1u));
    const long close_rc = syscall3(21, fd, 0, 0);
    const size_t expected_len = sizeof(TARGET_BYTES) - 1u;
    if (bytes < (long)expected_len || close_rc != 0 ||
        !same_prefix(marker, TARGET_BYTES, expected_len) ||
        (marker[expected_len] != '\n' && marker[expected_len] != '\0')) {
        write_text("NATIVE INIT ERROR: target rootfs marker OPEN/READ/CLOSE validation failed\n");
        exit_with(77);
    }

    write_text("NATIVE INIT ROOTFS VERIFIED: target=" TARGET_NAME "\n");
    write_text("NATIVE INIT BLOCKED: persistent storage and target service backends are unavailable\n");
    /* Exit 78 is intentional. Never synthesize USERSPACE READY while required
       target services and persistent storage are missing. */
    exit_with(78);
}
