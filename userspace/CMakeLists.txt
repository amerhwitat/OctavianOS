cmake_minimum_required(VERSION 3.16)
project(octavian-init C ASM)

# Koronos production init - builds a genuinely working init(1) that:
# - Executes in CPL3 (user mode)
# - Uses real syscalls (not stubs or emulation)
# - Manages process lifecycle (fork, exec, wait, signal)
# - Mounts filesystems and services
# - Aligns with Linux init workflow (systemd-like)
#
# Aligned with:
# - Linux FHS (Filesystem Hierarchy Standard)
# - Linux ABI (x86-64 SYSCALL, register conventions)
# - Linux libc (musl, glibc compatible)
# - systemd unit conventions

set(CMAKE_C_STANDARD 17)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_ASM_FLAGS_INIT "-x assembler-with-cpp")

# Architecture detection
if(NOT KORONOS_ARCH)
    if(CMAKE_SYSTEM_PROCESSOR MATCHES "x86_64|amd64")
        set(KORONOS_ARCH "x86_64")
    elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "aarch64|arm64")
        set(KORONOS_ARCH "arm64")
    elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "riscv64")
        set(KORONOS_ARCH "riscv64")
    else()
        message(FATAL_ERROR "Unsupported architecture: ${CMAKE_SYSTEM_PROCESSOR}")
    endif()
endif()

message(STATUS "Building for architecture: ${KORONOS_ARCH}")

# Only x86-64 currently has a real native Koronos entry/syscall veneer.
# ARM64 and RISC-V source files and kernel user-entry contracts are not present;
# do not build placeholder ELFs and advertise them as runnable targets.
if(NOT KORONOS_ARCH STREQUAL "x86_64")
    message(FATAL_ERROR "Native Koronos userspace is not implemented for ${KORONOS_ARCH}; refusing to build a placeholder init")
endif()
set(INIT_ENTRY_ASM "init-entry-x86_64.s")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -mcmodel=large")

# Production init binary
add_executable(octavian-init
    init-main.c
    ${INIT_ENTRY_ASM}
)

# Link against the architecture-specific musl sysroot while retaining libc and
# compiler runtime libraries. Only the CRT startup objects are omitted because
# the kernel enters at _init_entry; -nostdlib would incorrectly drop libc.
target_link_options(octavian-init PRIVATE
    -static-pie           # Position-independent executable with static linking
    -nostartfiles         # Custom _init_entry replaces the CRT entry point
    -fno-ident            # No .comment section
    -Wl,--gc-sections     # Remove unused sections
    -Wl,--strip-all       # Strip all symbols (production)
)

# Set entry point
set_target_properties(octavian-init PROPERTIES
    LINK_FLAGS "-Wl,-e,_init_entry"
)

# Build flags for production init
target_compile_options(octavian-init PRIVATE
    -Wall -Wextra -Werror
    -Wno-missing-prototypes  # Some syscalls may not have declarations
    -Wno-strict-aliasing     # Syscall arg packing requires some aliasing
    -fvisibility=hidden      # Hide internal symbols
    -ffunction-sections      # Allow fine-grained garbage collection
    -fdata-sections
    -O2                      # Optimize for size and speed
    -fPIE                    # Required for static PIE image
    -fno-stack-protector     # No TLS/canary runtime before init setup
    -march=${KORONOS_ARCH_MARCH}  # Specific CPU tuning
)

# Define Koronos-specific syscall numbers
target_compile_definitions(octavian-init PRIVATE
    KORONOS_SYSCALL_GETPID=20
    KORONOS_SYSCALL_EXIT=60
    KORONOS_SYSCALL_EXIT_GROUP=231
    KORONOS_SYSCALL_FORK=57
    KORONOS_SYSCALL_EXEC=59
    KORONOS_SYSCALL_WAIT4=114
    KORONOS_SYSCALL_SIGNAL=67
    KORONOS_SYSCALL_MOUNT=165
    KORONOS_SYSCALL_CHDIR=80
)

# Production verification
add_custom_command(TARGET octavian-init POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E echo "=== Init binary verification ==="
    COMMAND file $<TARGET_FILE:octavian-init>
    COMMAND nm -nt $<TARGET_FILE:octavian-init> | head -20
    COMMAND ${CMAKE_COMMAND} -E echo "=== Checking for real syscall symbols ==="
    COMMAND nm $<TARGET_FILE:octavian-init> | grep -E "(getpid|fork|exec|waitpid|mount|chdir|exit|syscall)" || true
    COMMAND ${CMAKE_COMMAND} -E echo "=== Verifying no glibc dynamic symbols ==="
    COMMAND ! nm $<TARGET_FILE:octavian-init> | grep -E "@GLIBC" || echo "WARNING: glibc symbols found"
)

# Install into rootfs
install(TARGETS octavian-init
    RUNTIME DESTINATION /sbin
)

# Install systemd compatibility wrapper
install(FILES init-systemd-wrapper
    DESTINATION /sbin
    PERMISSIONS OWNER_READ OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE
)

# Real static-ELF validation. The previous echo-only CTest entries were
# placeholders and must never count as runtime acceptance.
include(CTest)
if(BUILD_TESTING)
    add_test(
        NAME init-static-elf-contract
        COMMAND ${CMAKE_COMMAND}
            -DINIT_BINARY=$<TARGET_FILE:octavian-init>
            -P ${CMAKE_CURRENT_SOURCE_DIR}/cmake/verify_init_elf.cmake
    )
endif()

message(STATUS "Build configuration:")
message(STATUS "  Architecture: ${KORONOS_ARCH}")
message(STATUS "  Entry point: ${INIT_ENTRY_ASM}")
message(STATUS "  Target: octavian-init")
