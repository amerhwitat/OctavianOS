# Language and Binary Toolchain Support

OctavianOS vendors the ChimeraIIOS language/toolchain capability catalog at
`vendor/chimera-ii-os/source/toolchains/language-toolchain-catalog.json`.
The shared catalog describes 66 language families, compiler/interpreter
providers, assembler and disassembler families, linkers, binary utilities,
cross targets and optional package-manager installation profiles.

The catalog is mirrored with its validator, optional profile installer,
Aurora profile metadata, compiler matrix and CI tests. The OctavianOS
Chimera integration workflow validates the vendored catalog and runs a
non-installing package-plan check.

## Optional toolchain profiles

From the vendored source root:

```sh
python3 tools/toolchain/install-language-profile.py --list
python3 tools/toolchain/install-language-profile.py native-core --dry-run
python3 tools/toolchain/install-language-profile.py scripting --dry-run
```

After reviewing the package list, a user can explicitly install a profile
with `sudo python3 tools/toolchain/install-language-profile.py <profile> --yes`.
The installer supports apt, dnf and pacman. Package availability depends on
the distribution and enabled repositories.

The base OS image does not bundle every language ecosystem: doing so would
inflate the ISO substantially and would include components with different
licensing and update requirements. Toolchain profiles are opt-in. Proprietary
vendor compilers and assemblers remain external installations.

A catalog entry is not proof that a compiler is installed, that an interpreter
is runnable, or that a native ABI exists. Cross-compilation requires a
matching target backend, sysroot and linker. WebAssembly is a virtual-machine
target. Experimental Chimera C8192/R8192 backends are not claimed to be
provided by GCC or LLVM.


The current shared catalog also includes V, Odin, experimental Carbon, MATLAB and GNU Octave, Wolfram Language, SAS, Raku, Elm, Haxe, ReScript, Solidity, Vyper, Move, Verilog, SystemVerilog and VHDL. It inventories 13 assembler providers and 11 disassembly/reverse-engineering providers, including LLVM ML, external ARM/IAR assemblers, MSVC dumpbin and Apple Mach-O inspection tools.

A dedicated `hardware-description` profile provides opt-in package plans for Icarus Verilog, Verilator, GHDL and Yosys. Both ChimeraIIOS and OctavianOS declare the same `CHM-LANGUAGE-TOOLCHAIN-1` contract in the catalog's `operating_systems` section. This is catalog/profile integration, not a claim that all providers are bundled or that every target ABI has been implemented. Commercial MATLAB, Wolfram, SAS, MASM, ARM Compiler, IAR and Apple tools require external installation and applicable licenses; Carbon remains experimental.
