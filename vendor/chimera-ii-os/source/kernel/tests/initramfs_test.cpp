#include <cassert>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>

#include "chimera/initramfs.h"

namespace {
using Bytes = std::vector<uint8_t>;

void hex8(Bytes &out, uint32_t value) {
    static const char digits[] = "0123456789abcdef";
    for (int shift = 28; shift >= 0; shift -= 4)
        out.push_back(static_cast<uint8_t>(digits[(value >> shift) & 0xfu]));
}
void append_record(Bytes &out, const std::string &name, const Bytes &data,
                   bool crc = false, bool bad_crc = false) {
    const char *magic = crc ? "070702" : "070701";
    out.insert(out.end(), magic, magic + 6);
    const uint32_t checksum = crc
        ? [&]() { uint32_t sum = 0; for (uint8_t b : data) sum += b; return sum; }()
        : 0u;
    hex8(out, 1);                    // ino
    hex8(out, 0100644);              // mode
    hex8(out, 0); hex8(out, 0);      // uid, gid
    hex8(out, 1); hex8(out, 0);      // nlink, mtime
    hex8(out, static_cast<uint32_t>(data.size()));
    hex8(out, 0); hex8(out, 0);      // devmajor, devminor
    hex8(out, 0); hex8(out, 0);      // rdevmajor, rdevminor
    hex8(out, static_cast<uint32_t>(name.size() + 1));
    hex8(out, bad_crc ? checksum + 1u : checksum);
    out.insert(out.end(), name.begin(), name.end());
    out.push_back(0);
    while (out.size() & 3u) out.push_back(0);
    out.insert(out.end(), data.begin(), data.end());
    while (out.size() & 3u) out.push_back(0);
}
Bytes fake_elf() {
    Bytes elf(64, 0);
    elf[0] = 0x7f; elf[1] = 'E'; elf[2] = 'L'; elf[3] = 'F';
    elf[4] = 2; elf[5] = 1; elf[6] = 1;
    return elf;
}
Bytes archive(const std::string &path, bool crc = false, bool bad_crc = false,
              bool duplicate = false) {
    Bytes out;
    const Bytes elf = fake_elf();
    append_record(out, path, elf, crc, bad_crc);
    if (duplicate) append_record(out, path, elf, crc);
    append_record(out, "TRAILER!!!", {});
    return out;
}
int find(const Bytes &bytes, const char *path, const void **data, uint64_t *size) {
    return chimera_initramfs_find_elf(bytes.data(), bytes.size(), path, data, size);
}
}

int main() {
    const Bytes elf = fake_elf();
    const Bytes valid = archive("init");
    const void *found = nullptr;
    uint64_t size = 0;
    assert(find(valid, "init", &found, &size) == 0);
    assert(found != nullptr && size == elf.size());
    assert(std::memcmp(found, elf.data(), elf.size()) == 0);

    const Bytes crc_valid = archive("sbin/init", true);
    assert(find(crc_valid, "sbin/init", &found, &size) == 0);

    const Bytes bad_crc = archive("init", true, true);
    assert(find(bad_crc, "init", &found, &size) == -11);

    const Bytes duplicate = archive("init", false, false, true);
    assert(find(duplicate, "init", &found, &size) == -7);

    const Bytes traversal = archive("../init");
    assert(find(traversal, "init", &found, &size) == -6);

    const uint8_t gzip[] = {0x1f, 0x8b, 0x08, 0x00, 0, 0, 0, 0};
    found = reinterpret_cast<const void *>(static_cast<uintptr_t>(1));
    size = 99;
    assert(chimera_initramfs_find_elf(gzip, sizeof(gzip), "init", &found, &size) == -13);
    assert(found == nullptr && size == 0);

    Bytes truncated = valid;
    truncated.resize(115);
    assert(find(truncated, "init", &found, &size) != 0);

    return 0;
}
