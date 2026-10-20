#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "chimera/initramfs.h"

namespace {
using Bytes = std::vector<uint8_t>;

void put_hex(Bytes &out, uint32_t value) {
    char field[9];
    std::snprintf(field, sizeof(field), "%08x", value);
    out.insert(out.end(), field, field + 8);
}

void append_entry(Bytes &out, const char *name, uint32_t mode,
                  const Bytes &payload, uint32_t nlink = 1,
                  bool crc = false, uint32_t checksum_override = 0,
                  bool override_checksum = false) {
    const char *magic = crc ? "070702" : "070701";
    out.insert(out.end(), magic, magic + 6);
    put_hex(out, 1);                 // ino
    put_hex(out, mode);
    put_hex(out, 0);                 // uid
    put_hex(out, 0);                 // gid
    put_hex(out, nlink);
    put_hex(out, 0);                 // mtime
    put_hex(out, static_cast<uint32_t>(payload.size()));
    put_hex(out, 0); put_hex(out, 0); // devmajor/devminor
    put_hex(out, 0); put_hex(out, 0); // rdevmajor/rdevminor
    put_hex(out, static_cast<uint32_t>(std::strlen(name) + 1));
    uint32_t checksum = 0;
    for (uint8_t b : payload) checksum += b;
    put_hex(out, override_checksum ? checksum_override : (crc ? checksum : 0));
    assert(out.size() >= 110);
    out.insert(out.end(), name, name + std::strlen(name));
    out.push_back(0);
    while (out.size() & 3u) out.push_back(0);
    out.insert(out.end(), payload.begin(), payload.end());
    while (out.size() & 3u) out.push_back(0);
}

Bytes archive_for(const char *name, uint32_t mode, uint32_t nlink = 1,
                  bool corrupt_trailer = false, bool crc = false,
                  bool corrupt_checksum = false) {
    Bytes out;
    Bytes elf(64, 0);
    elf[0] = 0x7f; elf[1] = 'E'; elf[2] = 'L'; elf[3] = 'F';
    append_entry(out, name, mode, elf, nlink, crc,
                 corrupt_checksum ? 1u : 0u, corrupt_checksum);
    Bytes trailer_payload;
    if (corrupt_trailer) trailer_payload.push_back('x');
    append_entry(out, "TRAILER!!!", 0100000u, trailer_payload, 1, crc);
    return out;
}

bool rejected(const Bytes &archive, const char *path = "init") {
    const void *elf = reinterpret_cast<const void *>(1);
    uint64_t size = 1;
    return chimera_initramfs_find_elf(archive.data(), archive.size(), path, &elf, &size) != 0
        && elf == nullptr && size == 0;
}
}

int main() {
    const uint32_t regular = 0100000u | 0755u;
    const uint32_t symlink = 0120000u | 0777u;

    Bytes valid = archive_for("init", regular);
    const void *elf = nullptr;
    uint64_t size = 0;
    assert(chimera_initramfs_find_elf(valid.data(), valid.size(), "init", &elf, &size) == 0);
    assert(elf != nullptr && size == 64);
    assert(static_cast<const uint8_t *>(elf)[0] == 0x7f);

    assert(rejected(archive_for("init", symlink)));
    assert(rejected(archive_for("init", regular, 0)));
    assert(rejected(archive_for("init", regular, 1, true)));
    assert(rejected(archive_for("init", regular, 1, false, true, true)));

    Bytes gzip = {0x1f, 0x8b, 0x08, 0x00};
    assert(rejected(gzip));
    assert(rejected(Bytes(valid.begin(), valid.begin() + 80)));
    assert(rejected(archive_for("../init", regular)));

    std::puts("initramfs parser tests: PASS");
    return 0;
}
