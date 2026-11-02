# Language and Binary Toolchain Support

OctavianOS vendors the ChimeraIIOS language/toolchain capability catalog at
`vendor/chimera-ii-os/source/toolchains/language-toolchain-catalog.json`.
The shared catalog describes 49 language families, compiler/interpreter
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
