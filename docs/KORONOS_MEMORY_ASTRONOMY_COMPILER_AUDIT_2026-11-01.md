# Koronos memory, desktop astronomy and compiler parity audit — 2026-11-01

## Scope and status

This change removes the old 4-GiB *usable physical frame* ceiling for the x86-64 Koronos bootstrap and raises the initial direct-map/allocator window to 64 GiB. This is a deliberate first-stage ceiling, not unlimited RAM support. It is sized to the x86-64 architectural minimum of 36 physical-address bits. Memory above 64 GiB remains unavailable until the kernel implements CPUID-derived physical-width handling and a dynamically sized direct map or high-memory mapping API.

## Memory changes in this branch

- `KORONOS_FRAME_PHYS_LIMIT` is now `0x1000000000` (64 GiB).
- The 4-KiB frame allocator bitmap now indexes 16,777,216 frames. Its two bitmaps consume 4 MiB of static storage.
- The 32-bit Multiboot2 entry creates 64 one-GiB PDPT windows with 2-MiB leaves (32,768 PDEs), carrying the high physical-address dword when advancing beyond 4 GiB.
- The address-space clone copies all 64 identity-map page directories.
- User virtual mappings now start at 64 GiB so they do not overlap the enlarged supervisor identity/direct map.
- Added `kernel/tests/frame_allocator_highmem_test.cpp`: a host-side synthetic Multiboot2 memory map containing usable RAM only above 4 GiB; it verifies single-frame and contiguous allocation/free above 4 GiB.
- Native Koronos CI now runs that regression and rebuilds the freestanding kernel with Clang after the default GCC build.

The regression test proves allocator arithmetic and frame ownership for a synthetic high-memory map. It does **not** yet prove real QEMU/physical RAM access above 4 GiB, CPUID physical-width discovery, NUMA, hot-add/remove, DMA zones, page poisoning, or memory pressure/reclaim. Before production use, run a QEMU configuration with more than 4 GiB of RAM and have the kernel allocate, write, read and free pages above 4 GiB. The direct map currently uses broad 2-MiB identity leaves; a production memory subsystem still needs memory-type-aware mappings for MMIO and a high-half kernel mapping.

## Comparison with Linux and Windows memory managers

| Capability | Linux x86-64 | Windows x64 | Koronos after this change |
|---|---|---|---|
| Physical memory discovery | Firmware/boot memory map, architecture setup and memblock | Firmware/loader data and kernel memory manager | Multiboot2 memory-map tag |
| Physical frame metadata | FLATMEM/SPARSEMEM PFN metadata | PFN database | Two fixed bitmaps, capped at 64 GiB |
| Allocation | Buddy allocator, zones and per-CPU page sets | PFN database, pools and working-set/page lists | One locked first-fit bitmap |
| Kernel mapping | Direct map plus vmalloc/ioremap and high-half layout | System virtual address space and kernel pools | Low identity/direct map up to 64 GiB |
| User memory | Independent mm/page tables, demand paging, swap | Per-process virtual address spaces, working sets and pagefile | Small fixed-count address-space backend; no demand paging/swap |
| NUMA/hotplug | NUMA nodes and sparse memory support | Platform/version-dependent NUMA and hot-add features | Not implemented |

Linux's physical memory model explicitly accounts for discontiguous ranges and NUMA, and its x86-64 page-table layout uses a direct map distinct from user mappings. Its physical allocator uses zones, per-CPU page sets and buddy allocation. Windows likewise gives processes virtual address spaces distinct from total physical RAM, and uses pagefile-backed virtual memory and a PFN-based manager. Koronos is still a bootstrap allocator and mapping implementation, not equivalent to either mature manager.

References:
- Linux x86-64 memory map: https://kernel.org/doc/html/latest/arch/x86/x86_64/mm.html
- Linux physical memory model: https://www.kernel.org/doc/html/latest/mm/memory-model.html
- Linux physical memory/allocator: https://docs.kernel.org/mm/physical_memory.html
- Windows virtual address space and physical storage: https://learn.microsoft.com/en-us/windows/win32/memory/virtual-address-space-and-physical-storage
- Windows memory management: https://learn.microsoft.com/en-us/windows/win32/memory/about-memory-management

## Open-source astronomy desktop catalog

Added these upstream projects to `desktop/optional_apps_catalog.json` and exposed them in Aurora's optional-app browser and Marine's Start menu:

| Application | Primary use | License | Build system |
|---|---|---|---|
| Stellarium | Real-time planetarium | GPL-2.0-or-later | CMake |
| KStars + Ekos | Planetarium, observing planner and astrophotography/telescope control | GPL-2.0-or-later | CMake |
| Celestia | 3D space simulator | GPL-2.0-or-later | CMake |
| Gaia Sky | Scientific 3D universe visualization | MPL-2.0 | Gradle / Java |
| Siril | Astrophotography image processing | GPL-3.0-or-later | CMake |
| Gpredict | Satellite tracking and pass prediction | GPL-2.0-or-later | Autotools |

The Marine shortcuts link to the official project sites. The catalog records upstream source, build system, dependencies and an explicit `catalog-only` status. They are **not claimed to be installed, ported, or runnable natively**. Aurora's catalog UI labels them as external provider targets, not installed applications.

Upstream references:
- Stellarium: https://stellarium.org/ and https://github.com/stellarium/stellarium
- KStars: https://apps.kde.org/kstars/ and https://github.com/KDE/kstars
- Gaia Sky: https://gaiasky.space/ and https://gaiasky.space/licenses/
- Siril: https://siril.org/
- Celestia: https://celestiaproject.space/
- Gpredict: https://github.com/csete/gpredict

## Compiler status

The freestanding Koronos build script supports selecting `CXX`, `USER_CC`/ `CC`, `LD`, and `NASM`. CI now compiles once with GCC/G++ and performs a second clean freestanding build with Clang/Clang++ (GNU ld and NASM retained for the common link/assembly contract).

This validates source portability across two host-native compiler toolchains. It is **not** a self-hosting build performed by compilers running inside ChimeraIIOS and OctavianOS. Neither OS has yet demonstrated a booted native compiler toolchain that can build these third-party astronomical applications. Each app requires its upstream GUI, graphics, scientific and runtime dependencies to be ported before native compilation can be claimed.

## Release gates

- GCC and Clang Koronos build jobs must pass.
- High-memory allocator regression must pass.
- QEMU with more than 4 GiB must verify real allocations above 4 GiB and memory access, not just a synthetic map.
- BIOS and UEFI boot matrix must remain green.
- Astronomy entries remain explicitly unsupported until a native package provider, dependencies, build, launch and license notices are validated.
- No production ISO publication is authorized by this audit alone.


## Follow-up: real high-memory access probe

The kernel now exposes `koronos_frame_allocator_highmem_self_test()`. On a machine with usable memory above 4 GiB it allocates a frame above 4 GiB, writes and reads two 64-bit patterns through the identity/direct map, and frees the frame. If no usable RAM exists above 4 GiB the probe reports a skip; if the read/write/free test fails, Koronos marks frame initialization failed so the address-space backend remains disabled. Both repositories' Koronos boot workflows now request a 5-GiB QEMU guest and require the high-memory pass marker. The Octavian native build workflow also rebuilds with Clang/Clang++ after GCC/G++ and runs the synthetic allocator regression.


## Desktop and application-framework comparison

| Area | Windows implementation | Linux desktop implementation | Current Chimera/Octavian implementation |
|---|---|---|---|
| Shell/desktop | Explorer shell, Start menu, taskbar and Win32 window manager | GNOME Shell/KDE Plasma over Wayland or X11 | Aurora and Marine are HTML/CSS/JS desktop prototypes; Marine now exposes astronomy project links and Aurora consumes the optional-app catalog |
| App discovery | Start menu, MSIX/winget and registered application links | XDG desktop entries, package managers, Flatpak/AppImage and portals | JSON optional-app catalog with explicit external-provider/catalog-only states; no native astronomy package provider yet |
| Window/compositor | DWM, Win32 windowing and graphics stack | Wayland compositor, XDG portals and toolkit backends | Native compositor/window protocol and GPU driver integration remain incomplete |
| Background services | Windows Service Control Manager | systemd service units and D-Bus activation | Koronos service manifest/dependency state only; full process supervision is not complete |
| Astronomy apps | Windows builds exist for Stellarium, KStars, Celestia, Gaia Sky and Siril | Linux packages/source builds exist for the listed projects | Upstream links and build recipes are catalogued; no app is yet ported/compiled/launched natively |

The comparison is architectural rather than a claim of binary compatibility. Windows uses the Service Control Manager to maintain service records and start/stop service and driver processes; Linux VFS and desktop stacks rely on process-context filesystem calls, XDG launch metadata and compositor protocols. The OS desktop pages should not be described as equivalent to Explorer, GNOME or Plasma until their native window manager, compositor, accessibility, input, file associations, application lifecycle and package-provider contracts are implemented and tested.

References: https://learn.microsoft.com/en-us/windows/win32/services/service-control-manager ; https://docs.kernel.org/filesystems/vfs.html ; https://apps.kde.org/kstars/ ; https://stellarium.org/ .
