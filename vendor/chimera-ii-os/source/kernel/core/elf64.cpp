#include "../include/chimera/elf64.h"

static volatile uint32_t elf64_state;

extern "C" void koronos_elf64_init(void) {
    elf64_state = 0x454C4634u;
}

extern "C" int koronos_elf64_validate(const void *image, uint64_t size,
                                       uint16_t machine) {
    if (!image || size < sizeof(koronos_elf64_ehdr)) return 0;

    const auto *h = static_cast<const koronos_elf64_ehdr *>(image);
    if (!koronos_elf64_valid(h) ||
        h->e_ehsize < sizeof(koronos_elf64_ehdr) ||
        h->e_ehsize > size) return 0;
    if (h->e_machine != machine ||
        h->e_phentsize != sizeof(koronos_elf64_phdr)) return 0;

    // Validate by division before multiplication/addition. This avoids an
    // attacker-controlled program-header count/offset wrapping the end check.
    if (h->e_phoff > size) return 0;
    if (h->e_phnum != 0) {
        const uint64_t remaining = size - h->e_phoff;
        if (static_cast<uint64_t>(h->e_phnum) > remaining / h->e_phentsize)
            return 0;
    }
    return 1;
}
