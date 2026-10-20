#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define CHIMERA_CPIO_ABI 1u
#define CHIMERA_CPIO_MAX_NAME 4096u
typedef enum chimera_cpio_status {
 CHIMERA_CPIO_OK=0, CHIMERA_CPIO_INVALID=-1, CHIMERA_CPIO_NOT_FOUND=-2,
 CHIMERA_CPIO_NOT_REGULAR=-3, CHIMERA_CPIO_RANGE=-4, CHIMERA_CPIO_DUPLICATE=-5
} chimera_cpio_status;
typedef struct chimera_cpio_archive { const uint8_t *bytes; uint64_t size; uint32_t validated; } chimera_cpio_archive;
typedef struct chimera_cpio_file { const uint8_t *data; uint64_t size; uint32_t mode; } chimera_cpio_file;
/* Archive bytes remain owned by the boot module and must outlive every file view. */
int chimera_cpio_validate(chimera_cpio_archive *archive,const void *bytes,uint64_t size);
int chimera_cpio_find(const chimera_cpio_archive *archive,const char *path,chimera_cpio_file *out);
int chimera_cpio_read(const chimera_cpio_file *file,uint64_t offset,void *buffer,uint64_t capacity,uint64_t *read_count);
/* Read-only rootfs binding. The mounted archive borrows its bytes from the
   boot module, which must remain reserved for the lifetime of the mount. */
int chimera_vfs_mount_readonly(const void *bytes, uint64_t size);
int chimera_vfs_mount_boot_module(uint32_t module_kind);
int chimera_vfs_is_mounted(void);
int chimera_vfs_open_readonly(uint32_t pid, const char *path);
int chimera_vfs_read(uint32_t pid, int fd, void *kernel_buffer,
                     uint64_t capacity, uint64_t *read_count);
int chimera_vfs_close(uint32_t pid, int fd);
#ifdef __cplusplus
}
#endif
