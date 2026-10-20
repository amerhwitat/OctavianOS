#include <stdint.h>
#include <stddef.h>
#ifndef CHIMERA_INIT_TARGET
#error CHIMERA_INIT_TARGET must be set by the target build
#endif
#ifndef CHIMERA_INIT_TARGET_NAME
#error CHIMERA_INIT_TARGET_NAME must be set by the target build
#endif

static long call0(long number) {
  register long rax __asm__("rax") = number;
  __asm__ volatile("syscall" : "+a"(rax) : : "rcx", "r11", "memory");
  return rax;
}
static long call1(long number, long a) {
  register long rax __asm__("rax") = number;
  register long rdi __asm__("rdi") = a;
  __asm__ volatile("syscall" : "+a"(rax) : "D"(rdi) : "rcx", "r11", "memory");
  return rax;
}
static long call3(long number, long a, long b, long c) {
  register long rax __asm__("rax") = number;
  register long rdi __asm__("rdi") = a;
  register long rsi __asm__("rsi") = b;
  register long rdx __asm__("rdx") = c;
  __asm__ volatile("syscall" : "+a"(rax) : "D"(rdi), "S"(rsi), "d"(rdx) : "rcx", "r11", "memory");
  return rax;
}
static int matches_target(const char *actual, size_t actual_size) {
  static const char expected[] = CHIMERA_INIT_TARGET_NAME "\n";
  if (actual_size != sizeof(expected) - 1u) return 0;
  for (size_t i = 0; i < sizeof(expected) - 1u; ++i)
    if (actual[i] != expected[i]) return 0;
  return 1;
}
static long write_console(const char *p, long n) {
  register long rax __asm__("rax") = 9;
  register long rdi __asm__("rdi") = 1;
  register const char *rsi __asm__("rsi") = p;
  register long rdx __asm__("rdx") = n;
  __asm__ volatile("syscall" : "+a"(rax) : "D"(rdi), "S"(rsi), "d"(rdx) : "rcx", "r11", "memory");
  return rax;
}
static void write_pid_diagnostic(long pid) {
  char message[96];
  char reversed[20];
  static const char prefix[] = "NATIVE INIT PID: target=" CHIMERA_INIT_TARGET_NAME " pid=";
  size_t used = 0;
  for (size_t i = 0; i < sizeof(prefix) - 1u; ++i) message[used++] = prefix[i];
  unsigned long value = (unsigned long)pid;
  size_t digits = 0;
  while (value && digits < sizeof(reversed)) {
    reversed[digits++] = (char)('0' + (value % 10u));
    value /= 10u;
  }
  if (digits == 0 || used + digits + 1u > sizeof(message)) call1(1, 78);
  while (digits) message[used++] = reversed[--digits];
  message[used++] = '\n';
  if (write_console(message, (long)used) < 0) call1(1, 78);
}
__attribute__((noreturn, used)) void _start(void) {
  static const char started[] = "NATIVE INIT STARTED: " CHIMERA_INIT_TARGET_NAME "\n";
  static const char rootfs_verified[] = "NATIVE INIT ROOTFS VERIFIED: target=" CHIMERA_INIT_TARGET_NAME "\n";
  static const char rootfs_blocked[] = "NATIVE INIT BLOCKED: native read-only rootfs open/read/close validation failed; refusing readiness.\n";
  static const char blocked[] = "NATIVE INIT BLOCKED: required native storage, security, logging and graphics services are not available; refusing to claim USERSPACE READY.\n";
  static const char target_path[] = "/etc/chimera/target";
  /* DPL3 interrupt acknowledges the actual ring-3 origin; GETPID must come
     from the kernel-owned process record and may never be fabricated. */
  __asm__ volatile("int $0x80" ::: "memory");
  long pid = call0(2);
  if (pid <= 0) call1(1, 78);
  if (write_console(started, (long)(sizeof(started)-1)) < 0) call1(1, 78);
  write_pid_diagnostic(pid);

  /* Exercise the real read-only VFS path before making any service claim.
     OPEN accepts O_RDONLY only; READ copies into this process's writable
     stack; CLOSE must release the per-process descriptor. */
  long fd = call3(20, (long)target_path, 0, 0);
  char target_value[sizeof(CHIMERA_INIT_TARGET_NAME) + 1u];
  long bytes = fd >= 3 ? call3(8, fd, (long)target_value, (long)sizeof(target_value)) : fd;
  long close_rc = fd >= 3 ? call1(21, fd) : 0;
  if (fd < 3 || bytes != (long)sizeof(target_value) ||
      close_rc != 0 || !matches_target(target_value, (size_t)bytes)) {
    (void)write_console(rootfs_blocked, (long)(sizeof(rootfs_blocked)-1));
    call1(1, 78);
  }
  if (write_console(rootfs_verified, (long)(sizeof(rootfs_verified)-1)) < 0) call1(1, 78);

  if (write_console(blocked, (long)(sizeof(blocked)-1)) < 0) call1(1, 78);
  /* Exit 78 is an explicit unavailable-service result, not readiness. The
     production release gate must remain red until these services exist. */
  call1(1, 78);
  for (;;) __asm__ volatile("pause" ::: "memory");
}
