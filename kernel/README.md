# Koronos kernel (OctavianOS)

Koronos sources live in `vendor/chimera-ii-os/source/kernel`. This directory holds
only the Linux-style build entry point; `make -C kernel <target>` delegates to the
vendored kbuild tree (defconfig, menuconfig, all, modules, modules_install,
install, check, clean, mrproper, legacy).

The production userspace handoff gate remains blocked as documented in
`docs/ISO_RELEASE_ACCEPTANCE.md`; a successful build is not a boot acceptance.
