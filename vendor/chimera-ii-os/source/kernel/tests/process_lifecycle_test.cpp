#include <cassert>
#include <cstdint>
#include <cstring>
#include "chimera/process.h"

static void make_elf(uint8_t* bytes, uint64_t capacity) {
    std::memset(bytes, 0, static_cast<size_t>(capacity));
    auto* h = reinterpret_cast<koronos_elf64_ehdr*>(bytes);
    h->e_ident[0] = 0x7f; h->e_ident[1] = 'E'; h->e_ident[2] = 'L'; h->e_ident[3] = 'F';
    h->e_ident[4] = KORONOS_ELFCLASS64; h->e_ident[5] = KORONOS_ELFDATA2LSB;
    h->e_type = KORONOS_ET_DYN; h->e_machine = KORONOS_EM_X86_64;
    h->e_version = 1; h->e_entry = 0x400100; h->e_ehsize = sizeof(*h);
    h->e_phoff = sizeof(*h); h->e_phentsize = sizeof(koronos_elf64_phdr); h->e_phnum = 1;
    auto* p = reinterpret_cast<koronos_elf64_phdr*>(bytes + h->e_phoff);
    p->p_type = 1; p->p_flags = 5; p->p_offset = 0x1000; p->p_vaddr = 0x400000;
    p->p_filesz = 16; p->p_memsz = 0x2000; p->p_align = 4096;
    std::memset(bytes + 0x1000, 0x90, 16);
}

int main() {
    uint8_t elf[8192]{};
    make_elf(elf, sizeof(elf));
    assert(chimera_process_init() == 0);

    chimera_process_image parent_image{};
    chimera_process_handle parent{};
    assert(chimera_process_admit_elf_child(elf, sizeof(elf), KORONOS_EM_X86_64,
        0x800000, nullptr, &parent_image, &parent) > 0);
    assert(parent.pid == parent_image.pid && parent.generation != 0);

    chimera_process_image child_image{};
    chimera_process_handle child{};
    assert(chimera_process_admit_elf_child(elf, sizeof(elf), KORONOS_EM_X86_64,
        0x800000, &parent, &child_image, &child) > 0);
    assert(child.pid != parent.pid && child.generation != 0);

    chimera_process_handle grandchild{};
    chimera_process_image grandchild_image{};
    assert(chimera_process_admit_elf_child(elf, sizeof(elf), KORONOS_EM_X86_64,
        0x800000, &child, &grandchild_image, &grandchild) > 0);
    assert(chimera_process_count() == 3);
    assert(chimera_process_set_state(child.pid, CHIMERA_PROCESS_EXITED) < 0);

    chimera_process_handle reaped{};
    int32_t status = -999;
    assert(chimera_process_wait_child(parent, &reaped, &status) == 0);
    assert(chimera_process_exit(child, 23) == 0);
    assert(chimera_process_exit(child, 24) < 0);
    // An exited process cannot be reaped while it still owns an unreaped child.
    assert(chimera_process_wait_child(parent, &reaped, &status) == 0);
    assert(chimera_process_fault(grandchild, -11) == 0);
    assert(chimera_process_exit(grandchild, 31) < 0);
    chimera_process_image faulted_image{};
    assert(chimera_process_get_by_handle(grandchild, &faulted_image) == 0);
    assert(faulted_image.state == CHIMERA_PROCESS_FAULTED);
    chimera_process_handle reaped_grandchild{};
    assert(chimera_process_wait_child(child, &reaped_grandchild, &status) == 1);
    assert(reaped_grandchild.pid == grandchild.pid && status == -11);
    assert(chimera_process_get_by_handle(grandchild, &grandchild_image) < 0);
    assert(chimera_process_wait_child(parent, &reaped, &status) == 1);
    assert(reaped.pid == child.pid && reaped.generation == child.generation);
    assert(status == 23);
    assert(chimera_process_wait_child(parent, &reaped, &status) < 0);
    assert(chimera_process_get_by_handle(child, &child_image) < 0);
    assert(chimera_process_count() == 1);

    // Reinitialization must not erase a live parent or reset PID state.
    assert(chimera_process_init() == 0);
    assert(chimera_process_get_by_handle(parent, &parent_image) == 0);
    assert(chimera_process_count() == 1);

    chimera_process_handle replacement{};
    chimera_process_image replacement_image{};
    assert(chimera_process_admit_elf_child(elf, sizeof(elf), KORONOS_EM_X86_64,
        0x800000, &parent, &replacement_image, &replacement) > 0);
    assert(replacement.pid != child.pid);
    assert(chimera_process_get_by_handle(child, &child_image) < 0);
    assert(chimera_process_get_by_handle(replacement, &replacement_image) == 0);
    return 0;
}
