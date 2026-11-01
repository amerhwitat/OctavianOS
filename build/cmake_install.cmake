# Install script for directory: /mnt/c/tmp/ChimeraIIOS

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/usr/local")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "Release")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "1")
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

# Set path to fallback-tool for dependency-resolution.
if(NOT DEFINED CMAKE_OBJDUMP)
  set(CMAKE_OBJDUMP "/usr/bin/objdump")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE STATIC_LIBRARY FILES "/mnt/c/tmp/ChimeraIIOS/build/libchimera_cvel.a")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/chimera_vm" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/chimera_vm")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/chimera_vm"
         RPATH "")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE EXECUTABLE FILES "/mnt/c/tmp/ChimeraIIOS/build/chimera_vm")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/chimera_vm" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/chimera_vm")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/chimera_vm")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/virtualization" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/virtualization/cvel/cvel_registry.json"
    "/mnt/c/tmp/ChimeraIIOS/docs/virtualization/CVEL.md"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/chimera_kernel" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/chimera_kernel")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/chimera_kernel"
         RPATH "")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE EXECUTABLE FILES "/mnt/c/tmp/ChimeraIIOS/build/chimera_kernel")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/chimera_kernel" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/chimera_kernel")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/chimera_kernel")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/chimera" TYPE PROGRAM RENAME "aurora-session" FILES "/mnt/c/tmp/ChimeraIIOS/desktop/aurora/aurora-session.sh")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE PROGRAM RENAME "chimera-enable-startup" FILES "/mnt/c/tmp/ChimeraIIOS/tools/installer/enable-startup.sh")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/systemd/system" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/platform/systemd/chimera-kernel.service"
    "/mnt/c/tmp/ChimeraIIOS/platform/systemd/aurora-session@.service"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/wayland-sessions" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/platform/wayland/aurora.desktop")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/chimera_server" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/chimera_server")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/chimera_server"
         RPATH "")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE EXECUTABLE FILES "/mnt/c/tmp/ChimeraIIOS/build/chimera_server")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/chimera_server" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/chimera_server")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/chimera_server")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE STATIC_LIBRARY FILES "/mnt/c/tmp/ChimeraIIOS/build/libchimera_core.a")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE STATIC_LIBRARY FILES "/mnt/c/tmp/ChimeraIIOS/build/libchimera_machine.a")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/aurora_context_menu" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/aurora_context_menu")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/aurora_context_menu"
         RPATH "")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE EXECUTABLE FILES "/mnt/c/tmp/ChimeraIIOS/build/aurora_context_menu")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/aurora_context_menu" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/aurora_context_menu")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/aurora_context_menu")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/aurora" TYPE PROGRAM FILES
    "/mnt/c/tmp/ChimeraIIOS/desktop/aurora/aurora_flash_tool.py"
    "/mnt/c/tmp/ChimeraIIOS/desktop/aurora/aurora_flash_tool_gui.py"
    "/mnt/c/tmp/ChimeraIIOS/desktop/aurora/repository_application_center.py"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/applications" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/desktop/aurora/aurora-flash-tool.desktop"
    "/mnt/c/tmp/ChimeraIIOS/desktop/aurora/repository-application-center.desktop"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/aurora" TYPE PROGRAM FILES
    "/mnt/c/tmp/ChimeraIIOS/desktop/aurora/aurora_flash_tool.py"
    "/mnt/c/tmp/ChimeraIIOS/desktop/aurora/aurora_flash_tool_gui.py"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/applications" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/desktop/aurora/aurora-flash-tool.desktop")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/file-associations" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/desktop/file_associations/context_menu_registry.json")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/aurora_settings" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/aurora_settings")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/aurora_settings"
         RPATH "")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE EXECUTABLE FILES "/mnt/c/tmp/ChimeraIIOS/build/aurora_settings")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/aurora_settings" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/aurora_settings")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/aurora_settings")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/settings" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/desktop/aurora/aurora_settings_registry.json")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/media" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/desktop/aurora/aurora_media_ecosystem.json")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/aurora-media-player" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/aurora-media-player")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/aurora-media-player"
         RPATH "")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE EXECUTABLE FILES "/mnt/c/tmp/ChimeraIIOS/build/aurora-media-player")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/aurora-media-player" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/aurora-media-player")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/aurora-media-player")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/aurora-video-player" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/aurora-video-player")
    file(RPATH_CHECK
         FILE "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/aurora-video-player"
         RPATH "")
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE EXECUTABLE FILES "/mnt/c/tmp/ChimeraIIOS/build/aurora-video-player")
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/aurora-video-player" AND
     NOT IS_SYMLINK "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/aurora-video-player")
    if(CMAKE_INSTALL_DO_STRIP)
      execute_process(COMMAND "/usr/bin/strip" "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/bin/aurora-video-player")
    endif()
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/security" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/platform/pam/chimera-auth.conf")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/boot" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/boot/boot-menu-contract.json"
    "/mnt/c/tmp/ChimeraIIOS/boot/loader-menu.cfg"
    "/mnt/c/tmp/ChimeraIIOS/boot/boot_protocol.json"
    "/mnt/c/tmp/ChimeraIIOS/boot/mode_matrix.json"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/boot/jasper" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/boot/jasper/jasper.cfg"
    "/mnt/c/tmp/ChimeraIIOS/boot/jasper/live.cfg"
    "/mnt/c/tmp/ChimeraIIOS/boot/jasper/install.cfg"
    "/mnt/c/tmp/ChimeraIIOS/boot/jasper/recovery.cfg"
    "/mnt/c/tmp/ChimeraIIOS/boot/jasper/diagnostics.cfg"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/boot/menus" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/boot/spitfire/spitfire-menu.cfg"
    "/mnt/c/tmp/ChimeraIIOS/boot/installation/menu.cfg"
    "/mnt/c/tmp/ChimeraIIOS/boot/recovery/recovery-manifest.json"
    "/mnt/c/tmp/ChimeraIIOS/boot/diagnostics/diagnostics-manifest.json"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE PROGRAM FILES
    "/mnt/c/tmp/ChimeraIIOS/tools/runtime/chimera-nbit-mode.py"
    "/mnt/c/tmp/ChimeraIIOS/tools/runtime/chimera-nbitd.py"
    "/mnt/c/tmp/ChimeraIIOS/tools/runtime/chimera-neural-dim.py"
    "/mnt/c/tmp/ChimeraIIOS/tools/runtime/chimera-biometric-auth.py"
    "/mnt/c/tmp/ChimeraIIOS/desktop/aurora/aurora-nbit-top-panel.sh"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE PROGRAM FILES
    "/mnt/c/tmp/ChimeraIIOS/tools/media/file_metadata.py"
    "/mnt/c/tmp/ChimeraIIOS/tools/media/file_associations.py"
    "/mnt/c/tmp/ChimeraIIOS/tools/media/chimera_media.py"
    "/mnt/c/tmp/ChimeraIIOS/tools/media/playback.py"
    "/mnt/c/tmp/ChimeraIIOS/tools/media/aurora_media_player.py"
    "/mnt/c/tmp/ChimeraIIOS/tools/media/aurora_video_player.py"
    "/mnt/c/tmp/ChimeraIIOS/tools/build-live-boot-binaries.sh"
    "/mnt/c/tmp/ChimeraIIOS/tools/build-mobile-binaries.sh"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/file-associations" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/desktop/file_associations/file_property_schema.json"
    "/mnt/c/tmp/ChimeraIIOS/desktop/file_associations/file_association_registry.json"
    "/mnt/c/tmp/ChimeraIIOS/desktop/file_associations/mimeapps.list"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/applications" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/desktop/aurora/aurora-biometric-login.desktop")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/applications" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/desktop/aurora/aurora-files.desktop"
    "/mnt/c/tmp/ChimeraIIOS/desktop/aurora/aurora-media-player.desktop"
    "/mnt/c/tmp/ChimeraIIOS/desktop/aurora/aurora-video-player.desktop"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/isa" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/tools/isa/local_isa_catalog.json")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/cloud/providers.json"
    "/mnt/c/tmp/ChimeraIIOS/cloud/README.md"
    "/mnt/c/tmp/ChimeraIIOS/devops/README.md"
    "/mnt/c/tmp/ChimeraIIOS/devops/pipeline_schema.json"
    "/mnt/c/tmp/ChimeraIIOS/ai/README.md"
    "/mnt/c/tmp/ChimeraIIOS/ai/registry.json"
    "/mnt/c/tmp/ChimeraIIOS/ai/media/media_contract.json"
    "/mnt/c/tmp/ChimeraIIOS/docs/ai/AI_DISCIPLINES.md"
    "/mnt/c/tmp/ChimeraIIOS/docs/kernel/LINUX_7_2_2_COMPATIBILITY.md"
    "/mnt/c/tmp/ChimeraIIOS/docs/kernel/linux_feature_matrix.json"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/chimera/ai" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/include/chimera/ai/discipline.h"
    "/mnt/c/tmp/ChimeraIIOS/include/chimera/ai/media.h"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/infrastructure" TYPE DIRECTORY FILES
    "/mnt/c/tmp/ChimeraIIOS/infrastructure/kubernetes"
    "/mnt/c/tmp/ChimeraIIOS/infrastructure/openshift"
    "/mnt/c/tmp/ChimeraIIOS/infrastructure/openstack"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE PROGRAM FILES
    "/mnt/c/tmp/ChimeraIIOS/tools/cloud/chimera_cloud.py"
    "/mnt/c/tmp/ChimeraIIOS/tools/image/chimera_image.py"
    "/mnt/c/tmp/ChimeraIIOS/tools/media/chimera_media.py"
    "/mnt/c/tmp/ChimeraIIOS/tools/media/playback.py"
    "/mnt/c/tmp/ChimeraIIOS/tools/media/vision_mediapipe.py"
    "/mnt/c/tmp/ChimeraIIOS/tools/installer/install_cloud_platforms.sh"
    "/mnt/c/tmp/ChimeraIIOS/tools/installer/install_kubernetes.sh"
    "/mnt/c/tmp/ChimeraIIOS/tools/installer/install_openshift_tools.sh"
    "/mnt/c/tmp/ChimeraIIOS/tools/installer/install_openstack_tools.sh"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/applications" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/applications/catalog.json"
    "/mnt/c/tmp/ChimeraIIOS/applications/ecosystem/repos.json"
    "/mnt/c/tmp/ChimeraIIOS/applications/ecosystem/README.md"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/aurora" TYPE PROGRAM FILES "/mnt/c/tmp/ChimeraIIOS/desktop/aurora/aurora_crypto_center.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/applications" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/desktop/aurora/aurora-crypto-center.desktop"
    "/mnt/c/tmp/ChimeraIIOS/desktop/aurora/aurora_crypto_center.json"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/crypto" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/applications/crypto/crypto_ecosystem_registry.json")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE PROGRAM FILES
    "/mnt/c/tmp/ChimeraIIOS/tools/hosted/chimera-host-run.sh"
    "/mnt/c/tmp/ChimeraIIOS/tools/vmware/chimera-vmware.sh"
    "/mnt/c/tmp/ChimeraIIOS/tools/hosted/chimera-host-detect.sh"
    "/mnt/c/tmp/ChimeraIIOS/tools/hosted/install-chimera-host.sh"
    "/mnt/c/tmp/ChimeraIIOS/tools/dualboot/chimera-dualboot-linux.sh"
    "/mnt/c/tmp/ChimeraIIOS/tools/dualboot/chimera-dualboot-macos.sh"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/hosted" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/tools/hosted/chimera-host.json"
    "/mnt/c/tmp/ChimeraIIOS/tools/dualboot/chimera-dualboot-plan.json"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/hosted" TYPE PROGRAM FILES
    "/mnt/c/tmp/ChimeraIIOS/tools/hosted/chimera-host-run.ps1"
    "/mnt/c/tmp/ChimeraIIOS/tools/dualboot/chimera-dualboot-windows.ps1"
    "/mnt/c/tmp/ChimeraIIOS/tools/hyperv/chimera-hyperv.ps1"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/hypervisors" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/tools/hyperv/README.md"
    "/mnt/c/tmp/ChimeraIIOS/tools/vmware/README.md"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/ai" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/ai/nextgen/algorithms.json"
    "/mnt/c/tmp/ChimeraIIOS/ai/nextgen/algorithms_2026.json"
    "/mnt/c/tmp/ChimeraIIOS/ai/nextgen/hardware.json"
    "/mnt/c/tmp/ChimeraIIOS/ai/nextgen/iot_protocols.json"
    "/mnt/c/tmp/ChimeraIIOS/docs/ai/nextgen-2026.md"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/data" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/data/registry/databases.json"
    "/mnt/c/tmp/ChimeraIIOS/data/registry/hadoop.json"
    "/mnt/c/tmp/ChimeraIIOS/data/registry/openstack.json"
    "/mnt/c/tmp/ChimeraIIOS/data/registry/licenses.json"
    "/mnt/c/tmp/ChimeraIIOS/data/hadoop/hadoop_profile.json"
    "/mnt/c/tmp/ChimeraIIOS/data/openstack/openstack_profile.json"
    "/mnt/c/tmp/ChimeraIIOS/performance/registry/performance_profiles.json"
    "/mnt/c/tmp/ChimeraIIOS/performance/registry/repair_policies.json"
    "/mnt/c/tmp/ChimeraIIOS/performance/registry/scaffolds.json"
    "/mnt/c/tmp/ChimeraIIOS/network/protocols/ai_network_protocols.json"
    "/mnt/c/tmp/ChimeraIIOS/network/protocols/routing_protocols.json"
    "/mnt/c/tmp/ChimeraIIOS/network/protocols/edition_network_profiles.json"
    "/mnt/c/tmp/ChimeraIIOS/dashboard/kpis.json"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/network" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/data/network/gateways.json"
    "/mnt/c/tmp/ChimeraIIOS/data/network/chimera_nodes.json"
    "/mnt/c/tmp/ChimeraIIOS/data/network/discovered_hosts.json"
    "/mnt/c/tmp/ChimeraIIOS/data/network/peers.json"
    "/mnt/c/tmp/ChimeraIIOS/desktop/aurora/network_fabric.json"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/dashboard" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/dashboard/kpis.json"
    "/mnt/c/tmp/ChimeraIIOS/dashboard/edition_profiles.json"
    "/mnt/c/tmp/ChimeraIIOS/desktop/aurora/dashboard.json"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/chimera" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/installer/installer_profiles.json"
    "/mnt/c/tmp/ChimeraIIOS/include/chimera/ai/runtime.h"
    "/mnt/c/tmp/ChimeraIIOS/include/chimera/parallel/parallel.h"
    "/mnt/c/tmp/ChimeraIIOS/include/chimera/iot/iot.h"
    "/mnt/c/tmp/ChimeraIIOS/include/chimera/data/data.h"
    "/mnt/c/tmp/ChimeraIIOS/include/chimera/performance/performance.h"
    "/mnt/c/tmp/ChimeraIIOS/include/chimera/network/ai_network.h"
    "/mnt/c/tmp/ChimeraIIOS/include/chimera/dashboard/dashboard.h"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE PROGRAM FILES
    "/mnt/c/tmp/ChimeraIIOS/tools/ai/chimera_ai_runtime.py"
    "/mnt/c/tmp/ChimeraIIOS/tools/parallel/chimera_parallel.py"
    "/mnt/c/tmp/ChimeraIIOS/tools/iot/chimera_iot.py"
    "/mnt/c/tmp/ChimeraIIOS/tools/data/chimera_data.py"
    "/mnt/c/tmp/ChimeraIIOS/tools/data/hadoop_doctor.py"
    "/mnt/c/tmp/ChimeraIIOS/tools/data/openstack_doctor.py"
    "/mnt/c/tmp/ChimeraIIOS/tools/repair/chimera_repair.py"
    "/mnt/c/tmp/ChimeraIIOS/tools/scaffold/chimera_scaffold.py"
    "/mnt/c/tmp/ChimeraIIOS/tools/network/chimera_browser.py"
    "/mnt/c/tmp/ChimeraIIOS/tools/security/chimera_sentinel.py"
    "/mnt/c/tmp/ChimeraIIOS/tools/dashboard/chimera_dashboard.py"
    "/mnt/c/tmp/ChimeraIIOS/installer/chimera_installer.py"
    "/mnt/c/tmp/ChimeraIIOS/tools/build/build_all_editions.py"
    "/mnt/c/tmp/ChimeraIIOS/package/chimera_pkg.py"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE DIRECTORY FILES "/mnt/c/tmp/ChimeraIIOS/package/providers")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/scripts" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/installer/install-chimera.bat"
    "/mnt/c/tmp/ChimeraIIOS/installer/install-chimera.ps1"
    "/mnt/c/tmp/ChimeraIIOS/installer/install-chimera.sh"
    "/mnt/c/tmp/ChimeraIIOS/tools/build/build_all_editions.bat"
    "/mnt/c/tmp/ChimeraIIOS/tools/build/build_all_editions.ps1"
    "/mnt/c/tmp/ChimeraIIOS/tools/build/build_all_editions.sh"
    )
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/mnt/c/tmp/ChimeraIIOS/build/kernel/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/mnt/c/tmp/ChimeraIIOS/build/userland/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/mnt/c/tmp/ChimeraIIOS/build/installer/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/mnt/c/tmp/ChimeraIIOS/build/sdk/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/mnt/c/tmp/ChimeraIIOS/build/tools/chimera-asm/cmake_install.cmake")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/mnt/c/tmp/ChimeraIIOS/build/compat/windows/cmake_install.cmake")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE STATIC_LIBRARY FILES "/mnt/c/tmp/ChimeraIIOS/build/libchimera_registern.a")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/arch" TYPE DIRECTORY FILES "/mnt/c/tmp/ChimeraIIOS/arch/registern")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/tools" TYPE DIRECTORY FILES "/mnt/c/tmp/ChimeraIIOS/tools/chimera-asm")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/database" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/system/database/chimera-data-architecture.json")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/database" TYPE DIRECTORY FILES "/mnt/c/tmp/ChimeraIIOS/system/database/sql")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/database/schema" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/system/database/schema/chimera_mdm.sql")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/services" TYPE DIRECTORY FILES "/mnt/c/tmp/ChimeraIIOS/services/apache")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/web" TYPE DIRECTORY FILES "/mnt/c/tmp/ChimeraIIOS/web/runtime")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/web" TYPE PROGRAM FILES "/mnt/c/tmp/ChimeraIIOS/services/chimera-web/chimera_web.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/config" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/system/security/chimera_web_policy.json"
    "/mnt/c/tmp/ChimeraIIOS/system/containers/podman_profile.json"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/compat" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/compat/api-abi-registry.json")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/quadlet" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/system/containers/quadlet/chimera-web.container")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/systemd/system" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/platform/systemd/chimera-web.service")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE PROGRAM FILES "/mnt/c/tmp/ChimeraIIOS/tools/web/init-chimera-web-token.sh")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/web" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/services/chimera-web/README.md")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE PROGRAM FILES "/mnt/c/tmp/ChimeraIIOS/tools/build-boot-artifacts.sh")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/boot/jasper" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/boot/jasper/jasper_entry.asm"
    "/mnt/c/tmp/ChimeraIIOS/boot/jasper/jasper_main.cpp"
    "/mnt/c/tmp/ChimeraIIOS/boot/jasper/jasper.ld"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE PROGRAM FILES
    "/mnt/c/tmp/ChimeraIIOS/services/apache/install-apache-ecosystem.sh"
    "/mnt/c/tmp/ChimeraIIOS/services/apache/verify-apache-package.sh"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE PROGRAM FILES "/mnt/c/tmp/ChimeraIIOS/services/apache/apache-sync.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/apache" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/services/apache/apache-projects.json"
    "/mnt/c/tmp/ChimeraIIOS/services/apache/README.md"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/config" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/system/security/apache-sandbox.json")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE PROGRAM FILES
    "/mnt/c/tmp/ChimeraIIOS/tools/toolchain/chimera-cc"
    "/mnt/c/tmp/ChimeraIIOS/tools/toolchain/chimera-cxx"
    "/mnt/c/tmp/ChimeraIIOS/tools/toolchain/chimera-gas"
    "/mnt/c/tmp/ChimeraIIOS/tools/toolchain/chimera-ld"
    "/mnt/c/tmp/ChimeraIIOS/tools/toolchain/install-native-toolchain.sh"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/toolchains" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/toolchains/chimera-native-toolchain.json")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/boot" TYPE DIRECTORY FILES "/mnt/c/tmp/ChimeraIIOS/boot/splash")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/aurora" TYPE DIRECTORY FILES "/mnt/c/tmp/ChimeraIIOS/desktop/aurora/assets")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/aurora/config" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/config/aurora/font-packages.json"
    "/mnt/c/tmp/ChimeraIIOS/config/aurora/text-layout.json"
    "/mnt/c/tmp/ChimeraIIOS/config/aurora/language-font-map.json"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/aurora/docs" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/fonts/README.md"
    "/mnt/c/tmp/ChimeraIIOS/docs/aurora-rtl-ltr.md"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE PROGRAM FILES "/mnt/c/tmp/ChimeraIIOS/tools/build-font-pack.sh")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/aurora/config" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/config/aurora/media-players.json"
    "/mnt/c/tmp/ChimeraIIOS/config/aurora/media-associations.json"
    "/mnt/c/tmp/ChimeraIIOS/config/aurora/languages.json"
    "/mnt/c/tmp/ChimeraIIOS/config/aurora/font-fallback.json"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/aurora/docs" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/media/README.md"
    "/mnt/c/tmp/ChimeraIIOS/docs/aurora-multilingual-media.md"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE PROGRAM FILES "/mnt/c/tmp/ChimeraIIOS/tools/build-media-stack.sh")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/aurora/config" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/config/aurora/emulators.json"
    "/mnt/c/tmp/ChimeraIIOS/config/aurora/free-roms.json"
    "/mnt/c/tmp/ChimeraIIOS/config/aurora/emulator-windows.json"
    "/mnt/c/tmp/ChimeraIIOS/config/aurora/emulator-associations.json"
    "/mnt/c/tmp/ChimeraIIOS/config/aurora/desktop-parity.json"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/aurora/docs" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/docs/aurora-emulation.md"
    "/mnt/c/tmp/ChimeraIIOS/docs/kernel-desktop-implementation.md"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/config" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/config/chimera/kernel-desktop-parity.json"
    "/mnt/c/tmp/ChimeraIIOS/config/chimera/platform-feature-policy.json"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/drivers" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/config/drivers/driver-repositories.json"
    "/mnt/c/tmp/ChimeraIIOS/config/drivers/driver-policy.json"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/etc/chimera" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/config/drivers/driver-repositories.json"
    "/mnt/c/tmp/ChimeraIIOS/config/drivers/driver-policy.json"
    "/mnt/c/tmp/ChimeraIIOS/config/crash/chimera-crash-policy.json"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/etc/chimera" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/config/logging/chimera-logging.json")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/kore" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/system/kore/chimera-runtime-services.json")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/aurora" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/config/aurora/emulator-compression.json"
    "/mnt/c/tmp/ChimeraIIOS/config/aurora/playstation.json"
    "/mnt/c/tmp/ChimeraIIOS/config/aurora/rom-search.json"
    "/mnt/c/tmp/ChimeraIIOS/config/aurora/game-center.json"
    "/mnt/c/tmp/ChimeraIIOS/config/aurora/free-3d-games.json"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/aurora" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/system/aurora/chimera-crash-screen.json"
    "/mnt/c/tmp/ChimeraIIOS/system/aurora/chimera-playstation.desktop"
    "/mnt/c/tmp/ChimeraIIOS/system/aurora/chimera-rom-search.desktop"
    "/mnt/c/tmp/ChimeraIIOS/system/aurora/game-center-panel.json"
    "/mnt/c/tmp/ChimeraIIOS/system/aurora/chimera-free-3d-games.desktop"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/etc/chimera" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/system/boot/chimera-logging.conf")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/logging" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/config/logging/chimera-logging.json")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE PROGRAM FILES
    "/mnt/c/tmp/ChimeraIIOS/tools/chimera-driver-manager.sh"
    "/mnt/c/tmp/ChimeraIIOS/tools/chimera-driver-center.sh"
    "/mnt/c/tmp/ChimeraIIOS/tools/chimera-logd.sh"
    "/mnt/c/tmp/ChimeraIIOS/tools/chimera-logrotate.sh"
    "/mnt/c/tmp/ChimeraIIOS/tools/chimera-kmsg-forwarder.sh"
    "/mnt/c/tmp/ChimeraIIOS/tools/chimera-xexec.sh"
    "/mnt/c/tmp/ChimeraIIOS/tools/chimera-playstation-center.sh"
    "/mnt/c/tmp/ChimeraIIOS/tools/chimera-crash-dump.sh"
    "/mnt/c/tmp/ChimeraIIOS/tools/chimera-screen-of-death.sh"
    "/mnt/c/tmp/ChimeraIIOS/tools/chimera-memory-dump.sh"
    "/mnt/c/tmp/ChimeraIIOS/tools/chimera-rom-search.sh"
    "/mnt/c/tmp/ChimeraIIOS/tools/chimera-game-center.sh"
    "/mnt/c/tmp/ChimeraIIOS/tools/chimera-free-3d-games.sh"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/systemd/system" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/system/drivers/chimera-driver-manager.service"
    "/mnt/c/tmp/ChimeraIIOS/system/logging/chimera-logd.service"
    "/mnt/c/tmp/ChimeraIIOS/system/logging/chimera-logrotate.service"
    "/mnt/c/tmp/ChimeraIIOS/system/logging/chimera-logrotate.timer"
    "/mnt/c/tmp/ChimeraIIOS/system/logging/chimera-kmsg-forwarder.service"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/kernel/include/chimera" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/kernel/include/chimera/platform_features.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/emulators" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/system/emulators/README.md"
    "/mnt/c/tmp/ChimeraIIOS/docs/aurora-game-center.md"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE PROGRAM FILES "/mnt/c/tmp/ChimeraIIOS/tools/build-emulator-stack.sh")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/aurora" TYPE PROGRAM FILES "/mnt/c/tmp/ChimeraIIOS/desktop/aurora/aurora-session.sh")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/aurora/emulators/bin" TYPE PROGRAM FILES
    "/mnt/c/tmp/ChimeraIIOS/aurora/emulators/bin/aurora-emulator-window.sh"
    "/mnt/c/tmp/ChimeraIIOS/aurora/emulators/bin/launch-retro.sh"
    "/mnt/c/tmp/ChimeraIIOS/aurora/emulators/bin/launch-sakhr-ax170.sh"
    "/mnt/c/tmp/ChimeraIIOS/aurora/emulators/bin/launch-sakhr-ax230.sh"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/aurora/emulators" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/aurora/emulators/emulator-registry.json"
    "/mnt/c/tmp/ChimeraIIOS/aurora/emulators/binary-manifest.json"
    "/mnt/c/tmp/ChimeraIIOS/aurora/emulators/README.md"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/applications" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/aurora/emulators/desktop/chimera-sakhr-ax170.desktop"
    "/mnt/c/tmp/ChimeraIIOS/aurora/emulators/desktop/chimera-sakhr-ax230.desktop"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/boot" TYPE DIRECTORY FILES "/mnt/c/tmp/ChimeraIIOS/boot/visual")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE PROGRAM FILES
    "/mnt/c/tmp/ChimeraIIOS/tools/boot/chimera-boot-visual.sh"
    "/mnt/c/tmp/ChimeraIIOS/tools/boot/prepare-visual-assets.py"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/boot" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/boot/boot_protocol.json"
    "/mnt/c/tmp/ChimeraIIOS/boot/boot-artwork-manifest.json"
    "/mnt/c/tmp/ChimeraIIOS/boot/iso/grub.cfg"
    "/mnt/c/tmp/ChimeraIIOS/boot/iso/grub-theme.txt"
    "/mnt/c/tmp/ChimeraIIOS/boot/visual/boot-visual-manifest.json"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/applications" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/desktop/aurora/aurora-web-console.desktop")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/installer" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/installer/installation_phases.json"
    "/mnt/c/tmp/ChimeraIIOS/installer/installer_profiles.json"
    "/mnt/c/tmp/ChimeraIIOS/installer/chimera-installer-plan.json"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/mobile" TYPE DIRECTORY FILES "/mnt/c/tmp/ChimeraIIOS/mobile")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE PROGRAM FILES
    "/mnt/c/tmp/ChimeraIIOS/tools/flash/chimera-flash"
    "/mnt/c/tmp/ChimeraIIOS/mobile/android/build-mobile.sh"
    "/mnt/c/tmp/ChimeraIIOS/mobile/ios/build-mobile.sh"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/flash" TYPE FILE FILES
    "/mnt/c/tmp/ChimeraIIOS/tools/flash/flash-manifest.example.json"
    "/mnt/c/tmp/ChimeraIIOS/tools/flash/README.md"
    )
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/applications" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/system/aurora/chimera-hosted-bridge.desktop")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE PROGRAM RENAME "chimera-hosted" FILES "/mnt/c/tmp/ChimeraIIOS/tools/runtime/chimera-hosted.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/hosted" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/system/hosted/compatibility-matrix.json")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/bin" TYPE PROGRAM RENAME "chimera-isa-candidate" FILES "/mnt/c/tmp/ChimeraIIOS/tools/isa/chimera_isa_candidate.py")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/isa" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/isa/isa_database.json")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/chimera/isa/docs" TYPE FILE FILES "/mnt/c/tmp/ChimeraIIOS/docs/research/ISA_CANDIDATE_EXECUTION.md")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/mnt/c/tmp/ChimeraIIOS/build/tests/kernel/cmake_install.cmake")
endif()

string(REPLACE ";" "\n" CMAKE_INSTALL_MANIFEST_CONTENT
       "${CMAKE_INSTALL_MANIFEST_FILES}")
if(CMAKE_INSTALL_LOCAL_ONLY)
  file(WRITE "/mnt/c/tmp/ChimeraIIOS/build/install_local_manifest.txt"
     "${CMAKE_INSTALL_MANIFEST_CONTENT}")
endif()
if(CMAKE_INSTALL_COMPONENT)
  if(CMAKE_INSTALL_COMPONENT MATCHES "^[a-zA-Z0-9_.+-]+$")
    set(CMAKE_INSTALL_MANIFEST "install_manifest_${CMAKE_INSTALL_COMPONENT}.txt")
  else()
    string(MD5 CMAKE_INST_COMP_HASH "${CMAKE_INSTALL_COMPONENT}")
    set(CMAKE_INSTALL_MANIFEST "install_manifest_${CMAKE_INST_COMP_HASH}.txt")
    unset(CMAKE_INST_COMP_HASH)
  endif()
else()
  set(CMAKE_INSTALL_MANIFEST "install_manifest.txt")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  file(WRITE "/mnt/c/tmp/ChimeraIIOS/build/${CMAKE_INSTALL_MANIFEST}"
     "${CMAKE_INSTALL_MANIFEST_CONTENT}")
endif()
