#include <stdint.h>
#ifndef CHIMERA_INIT_TARGET
#error CHIMERA_INIT_TARGET must be set by the target build
#endif
#ifndef CHIMERA_INIT_TARGET_NAME
#error CHIMERA_INIT_TARGET_NAME must be set by the target build
#endif

#define CHIMERA_STRINGIFY_INNER(value) #value
#define CHIMERA_STRINGIFY(value) CHIMERA_STRINGIFY_INNER(value)

/* Build identity for packaging diagnostics only; this fail-closed bootstrap
 * is not a production init and is rejected by the release gate. */
__attribute__((used)) static const char target_identity[] =
    "CHIMERA_PRODUCTION_INIT_TARGET=" CHIMERA_STRINGIFY(CHIMERA_INIT_TARGET);

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
static long write_console(const char *p, long n) {
  register long rax __asm__("rax") = 9;
  register long rdi __asm__("rdi") = 1;
  register const char *rsi __asm__("rsi") = p;
  register long rdx __asm__("rdx") = n;
  __asm__ volatile("syscall" : "+a"(rax) : "D"(rdi), "S"(rsi), "d"(rdx) : "rcx", "r11", "memory");
  return rax;
}

/* Report the PID assigned by the kernel process manager. This is diagnostic
 * evidence only: a PID plus a syscall acknowledgement is not service readiness. */
static long write_pid_line(const char *target, long pid) {
  char line[128];
  const char prefix[] = "NATIVE INIT PID: target=";
  const char middle[] = " pid=";
  unsigned long value = (unsigned long)pid;
  char reversed[20];
  unsigned long digits = 0;
  long used = 0;
  for (unsigned long i = 0; i < sizeof(prefix) - 1; ++i) line[used++] = prefix[i];
  while (*target && used < (long)sizeof(line) - 24) line[used++] = *target++;
  for (unsigned long i = 0; i < sizeof(middle) - 1; ++i) line[used++] = middle[i];
  do { reversed[digits++] = (char)('0' + value % 10ul); value /= 10ul; }
  while (value && digits < sizeof(reversed));
  while (digits && used < (long)sizeof(line) - 2) line[used++] = reversed[--digits];
  line[used++] = '\n';
  return write_console(line, used);
}
__attribute__((noreturn, used)) void _start(void) {
  static const char started[] = "NATIVE INIT STARTED: " CHIMERA_INIT_TARGET_NAME "\n";
  static const char blocked[] = "NATIVE INIT BLOCKED: required native filesystem, process, device and graphics services are not available; refusing to claim USERSPACE READY.\n";
  /* DPL3 interrupt acknowledges the actual ring-3 origin; GETPID must come
     from the kernel-owned process record and may never be fabricated. */
  __asm__ volatile("int $0x80" ::: "memory");
  /* Native ABI CHM_SYS_GETPID=2 queries the PID already allocated when the
     kernel admitted and launched this ELF. Syscalls do not allocate PIDs;
     Linux x86-64 uses getpid=39, which is a separate compatibility ABI. */
  long pid = call0(2);
  if (pid <= 0) call1(1, 78);
  if (write_console(started, (long)(sizeof(started)-1)) < 0) call1(1, 78);
  if (write_pid_line(CHIMERA_INIT_TARGET_NAME, pid) < 0) call1(1, 78);
  if (write_console(blocked, (long)(sizeof(blocked)-1)) < 0) call1(1, 78);
  /* Exit 78 is an explicit unavailable-service result, not readiness. The
     production release gate must remain red until these services exist. */
  call1(1, 78);
  for (;;) __asm__ volatile("pause" ::: "memory");
}
