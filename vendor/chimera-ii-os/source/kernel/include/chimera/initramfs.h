#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
/* Strict bounded parser for uncompressed POSIX cpio newc/crc initramfs archives.
   Returns a pointer into the Multiboot module; it does not allocate or copy.
   The caller must keep the module mapped and validate the ELF before admission. */
int chimera_initramfs_find_elf(const void *archive, uint64_t archive_size,
                               const char *path, const void **elf_out,
                               uint64_t *elf_size_out);
#ifdef __cplusplus
}
#endif
