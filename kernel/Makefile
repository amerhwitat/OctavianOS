# OctavianOS Koronos kernel entry point.
#
# The authoritative kernel source tree is the vendored Chimera II snapshot. This
# Makefile keeps the Linux-style workflow (defconfig, menuconfig, modules,
# modules_install, install, check) available from the OctavianOS root without
# duplicating sources:
#
#   make -C kernel defconfig && make -C kernel -j"$(nproc)" && make -C kernel check
KDIR ?= $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../vendor/chimera-ii-os/source/kernel)

.DEFAULT_GOAL := all
.PHONY: all help defconfig menuconfig oldconfig savedefconfig modules modules_install install check clean mrproper legacy

all help defconfig menuconfig oldconfig savedefconfig modules modules_install install check clean mrproper legacy:
	@$(MAKE) --no-print-directory -C $(KDIR) $@
