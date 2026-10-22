#include <cassert>
#include <cstdint>
#include <cstring>
#include "chimera/multiboot_modules.h"

namespace {
alignas(8) uint8_t info[512];
uint32_t align8(uint32_t n) { return (n + 7u) & ~7u; }
uint32_t append_module(uint32_t off, uint32_t start, uint32_t end, const char *cmd) {
    const uint32_t size = 16u + static_cast<uint32_t>(std::strlen(cmd)) + 1u;
    const uint32_t type = 3u;
    std::memcpy(info + off, &type, 4);
    std::memcpy(info + off + 4, &size, 4);
    std::memcpy(info + off + 8, &start, 4);
    std::memcpy(info + off + 12, &end, 4);
    std::memcpy(info + off + 16, cmd, std::strlen(cmd) + 1u);
    return off + align8(size);
}
}
int main() {
    std::memset(info, 0, sizeof(info));
    uint32_t total = 0, reserved = 0;
    std::memcpy(info, &total, 4);
    std::memcpy(info + 4, &reserved, 4);
    uint32_t off = 8;
    off = append_module(off, 0x100000, 0x101000, "chimera-recovery-initramfs");
    off = append_module(off, 0x102000, 0x102400, "chimera-recovery-manifest");
    off = append_module(off, 0x103000, 0x104000, "chimera-live-initramfs");
    const uint32_t end_type = 0, end_size = 8;
    std::memcpy(info + off, &end_type, 4);
    std::memcpy(info + off + 4, &end_size, 4);
    off += 8;
    total = off;
    std::memcpy(info, &total, 4);
    assert(chimera_multiboot_scan(reinterpret_cast<uint64_t>(info)) == 3);
    assert(chimera_multiboot_find(CHIMERA_MODULE_RECOVERY_INITRAMFS) != nullptr);
    assert(chimera_multiboot_find(CHIMERA_MODULE_RECOVERY_MANIFEST) != nullptr);
    assert(chimera_multiboot_find(CHIMERA_MODULE_LIVE_INITRAMFS) != nullptr);
    assert(chimera_multiboot_find(CHIMERA_MODULE_INSTALL_IMAGE) == nullptr);

    // Exercise the exact module command-line labels emitted by the six-case
    // production-payload acceptance workflow. In particular, "profiles" must
    // use the same "installer-profiles" spelling as the classifier.
    std::memset(info, 0, sizeof(info));
    off = 8;
    off = append_module(off, 0x200000, 0x201000, "chimera-user-init-elf target=installer");
    off = append_module(off, 0x202000, 0x203000, "chimera-installation-image");
    off = append_module(off, 0x204000, 0x204100, "chimera-installation-manifest");
    off = append_module(off, 0x205000, 0x205100, "chimera-installer-contract");
    off = append_module(off, 0x206000, 0x206100, "chimera-install-phases");
    off = append_module(off, 0x207000, 0x207100, "chimera-installer-profiles");
    off = append_module(off, 0x208000, 0x208100, "chimera-install-profiles");
    std::memcpy(info + off, &end_type, 4);
    std::memcpy(info + off + 4, &end_size, 4);
    off += 8;
    total = off;
    std::memcpy(info, &total, 4);
    assert(chimera_multiboot_scan(reinterpret_cast<uint64_t>(info)) == 7);
    assert(chimera_multiboot_find(CHIMERA_MODULE_USER_INIT_ELF) != nullptr);
    assert(chimera_multiboot_find(CHIMERA_MODULE_INSTALL_IMAGE) != nullptr);
    assert(chimera_multiboot_find(CHIMERA_MODULE_INSTALL_MANIFEST) != nullptr);
    assert(chimera_multiboot_find(CHIMERA_MODULE_INSTALL_CONTRACT) != nullptr);
    assert(chimera_multiboot_find(CHIMERA_MODULE_INSTALL_PHASES) != nullptr);
    assert(chimera_multiboot_find(CHIMERA_MODULE_INSTALL_PROFILES) != nullptr);
    return 0;
}
