# WSL Windows-drive aliases

OctavianOS can optionally expose Windows drives already mounted by WSL under
`/mnt/c`, `/mnt/d`, etc. at `/mnt/drive/C`, `/mnt/drive/D`, etc.

Run `userspace/bin/octavian-map-windows-drives` after WSL automount has made
the source mount points available. It is deliberately a no-op outside WSL,
creates only missing symbolic links, is idempotent, and refuses to replace
an existing file, directory, or conflicting symlink.

This is a host-integration convenience layer, not a DrvFs implementation and
not a native Koronos NTFS driver. Windows filesystem semantics, metadata and
permissions remain those provided by WSL/DrvFs. It does not mount drives,
format partitions, or alter Windows data.

For isolated tests, the script accepts `CHM_WSL_FORCE=1`,
`CHM_MNT_ROOT`, and `CHM_DRIVE_ROOT` overrides.
