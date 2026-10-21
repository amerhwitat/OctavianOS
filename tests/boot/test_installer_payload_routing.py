#!/usr/bin/env python3
"""Static installer routing test; does not claim installer execution."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[2]
def require(ok,message):
 if not ok:raise SystemExit("installer routing regression: "+message)
def menu_block(text,menu_id):
 m=re.search(r'menuentry\s+"[^"]*"\s+--id\s+'+re.escape(menu_id)+r'\s*\{(.*?)\n\}',text,re.S)
 require(m is not None,f"menu entry --id {menu_id} is missing")
 return m.group(1)
def main():
 grub=(ROOT/"boot/iso/grub.cfg").read_text()
 jasper=(ROOT/"boot/jasper/jasper.cfg").read_text()
 installer=(ROOT/"boot/jasper/install.cfg").read_text()
 top=menu_block(grub,"install")
 for line in (
  "multiboot2 /boot/koronos/koronos.elf",
  "module2 /install/installer/installation.img chimera-installation-image",
  "module2 /install/installer/installation-manifest.json chimera-installation-manifest",
  "module2 /install/installer/installer-contract.json chimera-installer-contract",
  "module2 /install/installer/installation_phases.json chimera-install-phases",
  "module2 /install/installer/installer_profiles.json chimera-installer-profiles"):
  require(line in top,"top-level installer route missing: "+line)
 require("chimera-live-initramfs.img" not in top,"Install must not pass the Live initramfs")
 require("chimera-live-manifest.json" not in top,"Install must not pass the Live manifest")
 require("refusing to boot Live payload under the Install label" in top,"missing installer media must fail closed")
 jasper_install=menu_block(jasper,"chimera-install")
 require("configfile /boot/jasper/install.cfg" in jasper_install,"Jasper installer menu target must load install.cfg")
 native=menu_block(installer,"installer")
 require("module2 /install/installer/installation.img chimera-installation-image" in native,"Jasper installer image module missing")
 require("module2 /install/installer/installation-manifest.json chimera-installation-manifest" in native,"Jasper installer manifest missing")
 require("module2 /install/installer/installer-contract.json chimera-installer-contract" in native,"Jasper installer contract missing")
 require("chimera-live-initramfs.img" not in native,"installer path must not substitute Live initramfs")
 require("module2 /boot/installer/user-init-installer.elf chimera-user-init-elf target=installer" in native,"Jasper installer must launch target-specific native init")
 require(native.count("chimera-user-init-elf target=installer") == 1,"Jasper installer must stage exactly one native init ELF")
 legacy=menu_block(installer,"installer-legacy")
 require(legacy.count("chimera-user-init-elf target=installer") == 1,"legacy Jasper installer must stage exactly one native init ELF")
 print("installer routing static contract: PASS (module routing only; no installation-completion claim)")
if __name__=="__main__":main()
