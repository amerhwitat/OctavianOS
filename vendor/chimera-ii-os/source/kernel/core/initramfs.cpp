#include <stdint.h>
#include <stddef.h>
#include "chimera/initramfs.h"

namespace {
static uint32_t hex8(const uint8_t *p, bool *ok) {
    uint32_t value = 0;
    for (uint32_t i = 0; i < 8; ++i) {
        const uint8_t c = p[i];
        uint32_t digit;
        if (c >= '0' && c <= '9') digit = c - '0';
        else if (c >= 'a' && c <= 'f') digit = c - 'a' + 10u;
        else if (c >= 'A' && c <= 'F') digit = c - 'A' + 10u;
        else { *ok = false; return 0; }
        value = (value << 4) | digit;
    }
    return value;
}
static bool add_ok(uint64_t a, uint64_t b, uint64_t limit, uint64_t *out) {
    if (b > limit || a > limit - b) return false;
    *out = a + b;
    return true;
}
static bool same_path(const char *name, uint32_t name_size, const char *wanted) {
    uint32_t n = 0;
    while (wanted[n]) ++n;
    uint32_t start = (name_size && name[0] == '/') ? 1u : 0u;
    if (name_size && name[name_size - 1u] == 0) --name_size;
    if (name_size < start || name_size - start != n) return false;
    for (uint32_t i = 0; i < n; ++i) if (name[start + i] != wanted[i]) return false;
    return true;
}
}

extern "C" int chimera_initramfs_find_elf(const void *archive, uint64_t archive_size,
                                           const char *path, const void **elf_out,
                                           uint64_t *elf_size_out) {
    if (!archive || !path || !elf_out || !elf_size_out || archive_size < 110u ||
        archive_size > 64ull * 1024ull * 1024ull) return -1;
    *elf_out = nullptr;
    *elf_size_out = 0;
    const uint8_t *bytes = static_cast<const uint8_t *>(archive);
    uint64_t off = 0;
    bool found = false;
    bool trailer_seen = false;
    const void *candidate = nullptr;
    uint64_t candidate_size = 0;
    while (off <= archive_size && archive_size - off >= 110u) {
        const uint8_t *h = bytes + off;
        if (!((h[0]=='0' && h[1]=='7' && h[2]=='0' && h[3]=='7' &&
               h[4]=='0' && (h[5]=='1' || h[5]=='2')))) return -2;
        bool ok = true;
        const uint32_t file_size = hex8(h + 54, &ok);
        const uint32_t name_size = hex8(h + 94, &ok);
        const uint32_t expected_check = hex8(h + 102, &ok);
        if (!ok || name_size < 1u || name_size > 4096u) return -3;
        uint64_t name_start;
        if (!add_ok(off, 110u, archive_size, &name_start)) return -4;
        uint64_t name_end;
        if (!add_ok(name_start, name_size, archive_size, &name_end)) return -4;
        if (bytes[name_end - 1u] != 0) return -5;
        for (uint32_t i = 0; i + 1u < name_size; ++i) {
            if (bytes[name_start + i] == 0) return -5;
            if (bytes[name_start + i] == '.' && i + 1u < name_size &&
                bytes[name_start + i + 1u] == '.' &&
                (i == 0 || bytes[name_start + i - 1u] == '/')) return -6;
        }
        uint64_t data_start = (name_end + 3u) & ~3ull;
        if (data_start < name_end || data_start > archive_size) return -4;
        uint64_t data_end;
        if (!add_ok(data_start, file_size, archive_size, &data_end)) return -4;
        uint64_t next = (data_end + 3u) & ~3ull;
        if (next < data_end || next > archive_size) return -4;
        if (h[5] == '2') {
            uint32_t checksum = 0;
            for (uint64_t i = data_start; i < data_end; ++i)
                checksum += bytes[i];
            if (checksum != expected_check) return -11;
        } else if (expected_check != 0u) {
            return -12;
        }
        if (same_path(reinterpret_cast<const char *>(bytes + name_start), name_size, "TRAILER!!!")) {
            trailer_seen = true;
            break;
        }
        if (same_path(reinterpret_cast<const char *>(bytes + name_start), name_size, path)) {
            if (found) return -7;
            if (file_size < 64u || bytes[data_start] != 0x7f || bytes[data_start+1] != 'E' ||
                bytes[data_start+2] != 'L' || bytes[data_start+3] != 'F') return -8;
            found = true;
            candidate = bytes + data_start;
            candidate_size = file_size;
        }
        off = next;
    }
    if (!trailer_seen) return -10;
    if (!found) return -9;
    *elf_out = candidate;
    *elf_size_out = candidate_size;
    return 0;
}
