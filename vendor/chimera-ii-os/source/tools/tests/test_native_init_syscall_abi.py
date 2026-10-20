#!/usr/bin/env python3
"""Guard the stable native syscall IDs against placeholder mount/devctl aliases.

This is a source-contract test, not proof that the native process lifecycle or
any userspace service backend is implemented.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
HEADER = ROOT / "kernel/include/chimera/syscall.h"
DISPATCH = ROOT / "kernel/core/syscall.cpp"


def fail(message: str) -> int:
    print(f"NATIVE SYSCALL ABI FAIL: {message}", file=sys.stderr)
    return 1


def main() -> int:
    header = HEADER.read_text(encoding="utf-8")
    dispatcher = DISPATCH.read_text(encoding="utf-8")
    enum_match = re.search(
        r"enum\s+chimera_native_syscall\s*\{(?P<body>.*?)\};",
        header,
        re.DOTALL,
    )
    if not enum_match:
        return fail("native syscall enum is missing")
    entries = {
        name: int(value)
        for name, value in re.findall(
            r"\b(CHM_SYS_[A-Z0-9_]+)\s*=\s*(\d+)", enum_match.group("body")
        )
    }
    expected = {
        "CHM_SYS_EXIT": 1,
        "CHM_SYS_GETPID": 2,
        "CHM_SYS_YIELD": 3,
        "CHM_SYS_TIME_TICKS": 4,
        "CHM_SYS_READ": 8,
        "CHM_SYS_WRITE": 9,
        "CHM_SYS_MMAP": 10,
        "CHM_SYS_MUNMAP": 11,
        "CHM_SYS_IOCTL": 12,
        "CHM_SYS_NANOSLEEP": 13,
        "CHM_SYS_WAIT": 14,
        "CHM_SYS_ARCH_PRCTL": 15,
        "CHM_SYS_EXIT_GROUP": 16,
        "CHM_SYS_FORK": 17,
        "CHM_SYS_EXECVE": 18,
        "CHM_SYS_WAITPID": 19,
    }
    if entries != expected:
        return fail(f"native syscall table changed unexpectedly: {entries!r}")
    if "CHM_SYS_MOUNT" in header or "CHM_SYS_DEVCTL" in header:
        return fail("unimplemented mount/devctl IDs must not alias stable native syscall IDs")

    native_dispatch_start = dispatcher.find('extern "C" uint64_t koronos_syscall_user_dispatch')
    if native_dispatch_start < 0:
        return fail("native process-bound syscall dispatcher is missing")
    native_dispatch = dispatcher[native_dispatch_start:]
    if "case CHM_SYS_MMAP:" in native_dispatch or "case CHM_SYS_MUNMAP:" in native_dispatch:
        return fail("MMAP/MUNMAP unexpectedly acquired unreviewed dispatcher implementations")
    if "case CHM_SYS_GETPID:" not in native_dispatch or "case CHM_SYS_WRITE:" not in native_dispatch:
        return fail("native GETPID/WRITE support required by the current init handshake is missing")
    if "case CHM_SYS_MOUNT:" in native_dispatch or "case CHM_SYS_DEVCTL:" in native_dispatch:
        return fail("unsupported mount/devctl placeholder was added to the native dispatcher")

    print("NATIVE SYSCALL ABI PASS: stable IDs preserved; no mount/devctl alias accepted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
