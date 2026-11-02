#include <stdint.h>
#include "chimera/address_space.h"
#include "chimera/target_launch.h"

namespace {
static void debugcon_byte(uint8_t value) {
    __asm__ volatile("outb %0, $0xE9" : : "a"(value));
}
}
extern "C" void koronos_target_log(const char *message) {
    if (!message) return;
    while (*message) debugcon_byte(static_cast<uint8_t>(*message++));
    debugcon_byte(static_cast<uint8_t>('\n'));
}

/* Read only from the active process's validated user mapping. The readiness
 * recognizer receives a kernel copy, never an unchecked user pointer. */
extern "C" int64_t koronos_console_write_user(uint64_t address, uint64_t length) {
    if (!address || !length || length > 4096u) return -22;
    const uint32_t pid = koronos_target_active_pid();
    const uint64_t root = koronos_address_space_current_root();
    if (!pid || !root ||
        koronos_address_space_validate_user_range(root, address, length, 0) != 0)
        return -14;
    char buffer[4096];
    const auto *user = reinterpret_cast<const volatile uint8_t *>(
        static_cast<uintptr_t>(address));
    for (uint64_t i = 0; i < length; ++i) buffer[i] = static_cast<char>(user[i]);
    (void)koronos_target_note_user_write(buffer, length);
    for (uint64_t i = 0; i < length; ++i)
        debugcon_byte(static_cast<uint8_t>(buffer[i]));
    return static_cast<int64_t>(length);
}
