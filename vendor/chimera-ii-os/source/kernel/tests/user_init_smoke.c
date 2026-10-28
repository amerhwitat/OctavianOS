#include <stddef.h>

#if defined(CHIMERA_TARGET_LIVE)
#define CHIMERA_TARGET_NAME "live"
#elif defined(CHIMERA_TARGET_INSTALLER)
#define CHIMERA_TARGET_NAME "installer"
#elif defined(CHIMERA_TARGET_RECOVERY)
#define CHIMERA_TARGET_NAME "recovery"
#else
#error "Select CHIMERA_TARGET_LIVE, CHIMERA_TARGET_INSTALLER, or CHIMERA_TARGET_RECOVERY"
#endif

static long native_syscall3(long number, long a0, long a1, long a2) {
    register long result __asm__("rax") = number;
    register long arg0 __asm__("rdi") = a0;
    register long arg1 __asm__("rsi") = a1;
    register long arg2 __asm__("rdx") = a2;
    __asm__ volatile("syscall"
                     : "+a"(result)
                     : "D"(arg0), "S"(arg1), "d"(arg2)
                     : "rcx", "r11", "memory");
    return result;
}

static int vfs_seek_roundtrip(void) {
    static const char path[] = "/etc/chimera/target";
    char first = 0, second = 0;
    const long fd = native_syscall3(20, (long)path, 0, 0); /* OPEN, O_RDONLY */
    if (fd < 3) return -1;
    const long first_read = native_syscall3(8, fd, (long)&first, 1); /* READ */
    const long rewind = native_syscall3(22, fd, 0, 0); /* SEEK_SET */
    const long second_read = native_syscall3(8, fd, (long)&second, 1);
    const long close_rc = native_syscall3(21, fd, 0, 0); /* CLOSE */
    if (first_read != 1 || rewind != 0 || second_read != 1 ||
        first != second || close_rc != 0) return -1;
    return 0;
}

__attribute__((noreturn, used)) void _start(void) {
#if defined(CHIMERA_TEST_HANG)
    /* Deliberately hostile acceptance payload: no syscalls, no readiness,
       and no voluntary yield. Only a hardware IRQ-backed kernel deadline can
       regain control from this loop. */
    for (;;) __asm__ volatile("pause" ::: "memory");
#endif
    /* INT 0x80 enters a DPL3 IDT gate. The kernel acknowledgement is emitted
       only after checking the CPU-saved CS.RPL==3 and the active process CR3.
       This is distinct from SYSCALL, which does not save caller CS. */
    __asm__ volatile("int $0x80" ::: "memory");
    /* Ask the active kernel process record for our PID. Never bake PID 1 into
       the user image: this must keep working when process allocation changes. */
    register long number __asm__("rax") = 2; /* CHM_SYS_GETPID */
    __asm__ volatile("syscall"
                     : "+a"(number)
                     :
                     : "rcx", "r11", "memory");
    if (number <= 0) {
        number = 1; /* CHM_SYS_EXIT */
        register long failure_code __asm__("rdi") = 1;
        __asm__ volatile("syscall"
                         : "+a"(number)
                         : "D"(failure_code)
                         : "rcx", "r11", "memory");
        for (;;) __asm__ volatile("pause" ::: "memory");
    }

    /* Exercise the real mounted CPIO descriptor path before the probe reports readiness. */
    if (vfs_seek_roundtrip() != 0) {
        register long failure_number __asm__("rax") = 1;
        register long failure_code __asm__("rdi") = 1;
        __asm__ volatile("syscall" : "+a"(failure_number) : "D"(failure_code) : "rcx", "r11", "memory");
        for (;;) __asm__ volatile("pause" ::: "memory");
    }

    char ready_message[96];
    const char prefix[] = "USERSPACE READY: target=" CHIMERA_TARGET_NAME " init_pid=";
    size_t used = 0;
    for (size_t i = 0; i < sizeof(prefix) - 1u; ++i)
        ready_message[used++] = prefix[i];

    char reversed[20];
    size_t digits = 0;
    unsigned long pid = (unsigned long)number;
    while (pid && digits < sizeof(reversed)) {
        reversed[digits++] = (char)('0' + (pid % 10u));
        pid /= 10u;
    }
    if (digits == 0 || used + digits + 2u > sizeof(ready_message)) {
        number = 1;
        register long failure_code __asm__("rdi") = 1;
        __asm__ volatile("syscall"
                         : "+a"(number)
                         : "D"(failure_code)
                         : "rcx", "r11", "memory");
        for (;;) __asm__ volatile("pause" ::: "memory");
    }
    while (digits) ready_message[used++] = reversed[--digits];
    ready_message[used++] = '\n';

    /* Probe-only PID diagnostic: this proves the user image can report the
     * actual GETPID return value. It does not represent service readiness. */
    char pid_message[96];
    const char pid_prefix[] = "NATIVE INIT PID: target=" CHIMERA_TARGET_NAME " pid=";
    size_t pid_used = 0;
    for (size_t i = 0; i < sizeof(pid_prefix) - 1u; ++i)
        pid_message[pid_used++] = pid_prefix[i];
    char pid_reversed[20];
    size_t pid_digits = 0;
    unsigned long diagnostic_pid = (unsigned long)number;
    while (diagnostic_pid && pid_digits < sizeof(pid_reversed)) {
        pid_reversed[pid_digits++] = (char)('0' + (diagnostic_pid % 10u));
        diagnostic_pid /= 10u;
    }
    while (pid_digits) pid_message[pid_used++] = pid_reversed[--pid_digits];
    pid_message[pid_used++] = '\n';
    register long pid_write_number __asm__("rax") = 9;
    register long pid_write_fd __asm__("rdi") = 1;
    register const char *pid_write_buffer __asm__("rsi") = pid_message;
    register long pid_write_length __asm__("rdx") = (long)pid_used;
    __asm__ volatile("syscall"
                     : "+a"(pid_write_number)
                     : "D"(pid_write_fd), "S"(pid_write_buffer), "d"(pid_write_length)
                     : "rcx", "r11", "memory");

    number = 9; /* CHM_SYS_WRITE */
    register long fd __asm__("rdi") = 1;
    register const char *buffer __asm__("rsi") = ready_message;
    register long length __asm__("rdx") = (long)used;
    __asm__ volatile("syscall"
                     : "+a"(number)
                     : "D"(fd), "S"(buffer), "d"(length)
                     : "rcx", "r11", "memory");

    /* This second write proves the native syscall returned to ring 3. */
    static const char returned_message[] = "USERSPACE SYSCALL RETURNED TO RING3\n";
    number = 9;
    fd = 1;
    buffer = returned_message;
    length = (long)(sizeof(returned_message) - 1u);
    __asm__ volatile("syscall"
                     : "+a"(number)
                     : "D"(fd), "S"(buffer), "d"(length)
                     : "rcx", "r11", "memory");

    number = 1; /* CHM_SYS_EXIT */
    fd = 0;
    __asm__ volatile("syscall"
                     : "+a"(number)
                     : "D"(fd)
                     : "rcx", "r11", "memory");
    for (;;) __asm__ volatile("pause" ::: "memory");
}
