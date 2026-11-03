# Storage, networking, SDK and architecture integration

## ISO composition

The Octavian live image is a Linux-kernel live edition. It stages the desktop,
first-party app sources and catalogs, the pinned Chimera SDK source, and compiled
SDK artifacts when a build host provides the required toolchains. It does not
claim that source-only vendor components are installed executables.

## Filesystems and devices

The live edition uses Linux kernel filesystem drivers and userspace tools. The
image includes filesystem utilities for ext2/3/4, XFS, Btrfs, FAT/VFAT, exFAT,
NTFS, SquashFS, ISO-9660 and UDF, plus NFS/CIFS clients. Kernel support is still
dependent on the selected Debian kernel configuration/modules.

- `/dev` is populated by devtmpfs/udev.
- `/proc` and `/sys` are mounted by the Linux init system.
- `/tmp` is writable with sticky-bit permissions.
- Removable media is discovered by udev and mounted under `/media`.
- CD/DVD and ISO-9660/UDF media are always mounted read-only.
- Removable writable filesystems use `nosuid,nodev,noexec`; no automatic format
  or repair is performed.
- `chimera-media-manager.sh --mount-iso FILE` loop-mounts an ISO read-only.
- A root account exists but is locked by default; use the live user and sudo.

The native Koronos VFS is a separate project. A Linux live image is not evidence
that Koronos has mounted these filesystems. Native Koronos still needs a real VFS,
CPIO-to-root publication, mount namespaces, file descriptors, filesystem backends,
permission enforcement, journal/recovery and persistent-write tests.

## Networking

The image includes Linux networking utilities and optional routing/SDN stacks:
IPv4/IPv6, TCP/UDP, ICMP, iproute2, nftables, FRRouting, BIRD, Open vSwitch,
WireGuard, IPsec/OpenVPN, bridge/tc tools, DNS/DHCP clients, packet capture and
diagnostics. Dynamic routing daemons are installed but not enabled by default.
Configure and validate routing policies explicitly before enabling BGP/OSPF/IS-IS.

This does not implement a Koronos-native network stack. That requires NIC drivers,
DMA-safe RX/TX rings, interrupt/NAPI-like polling, socket ABI, IPv4/IPv6, routing
information/FIB transactions, neighbour discovery, firewall hooks and protocol
conformance tests.

## CISC/RISC hardware

Current official live-image boot output is x86_64/amd64. The vendored Koronos
tree contains x86_64 build artifacts and AArch64/RISC-V port scaffolding; that is
not multi-architecture boot acceptance. ARM64 and RV64 require their own
bootloader/EFI binaries, kernel entry, MMU, interrupt controller, timers, syscall
ABI, DMA/IOMMU and matching userspace ELF builds.

Endianness is explicit in disk/network wire formats. CPU endianness, ELF machine
and ABI are validated before selecting a binary. PCI/PCIe, ACPI and Device Tree
discovery are architecture/platform-specific; DMA mapping and cache-coherency
must be provided by the native kernel, not inferred from CPU family names.

## SDKs and IDEs

The image includes available C/C++, Java, Python, Rust, Go, Fortran, JavaScript,
Ruby, PHP and Lua toolchains plus Geany, Thonny, Emacs and Vim. Additional IDEs
and proprietary SDKs are optional host/provider integrations. Apple SDK payloads
are never redistributed by this repository.
