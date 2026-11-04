# Registry, Microsoft network interoperability and storage layout

## Registry settings and Aurora editor

CHMRG01 stores versioned typed settings in separate machine, environment and kernel hives. The Aurora Registry Editor is a loopback-only web UI at 127.0.0.1:8765 backed by registryd over a Unix socket. The daemon checks Unix peer credentials and chimera-admin group membership. Writes are generation-checked, journaled and atomically persisted. Hardware identity, discovered CPU features, privilege policy, memory limits, SMP acknowledgements and other boot-critical values remain immutable through the editor. The editor API requires a per-user runtime capability token; the browser receives it only through the user-session launcher. Never put passwords, Kerberos tickets, hashes or private keys in registry values.

## SMB and Microsoft network browsing

Use maintained Samba smbclient/smbd rather than a new SMB protocol stack. SMB2/3 only, mandatory signing, guest access disabled and NetBIOS/SMB1 disabled. Local-link browsing combines DNS-SD _smb._tcp and WS-Discovery; listing a server's shares is an explicit-target operation authenticated through the Kerberos credential cache. GVFS backends provide SMB URLs to compatible file managers. Server mode is opt-in and has no default shares or exposed interfaces.

## Active Directory and LDAP

directory-discovery.py performs bounded DNS SRV lookups for LDAP/Kerberos domain controllers. directoryctl.py uses realmd + adcli + SSSD for administrator-authorized domain join, and ldapsearch with GSSAPI and certificate validation for directory queries. A join changes machine identity and system authentication configuration; it is never automatic. Credentials remain in Kerberos/keyring facilities, not registry files or command-line password arguments.

## ISO/CD/DVD

mount-image.py validates ISO-9660/UDF images and requests read-only loop mounts through udisks2. Physical optical drives are limited to /dev/srN and mounted read-only. Polkit decides which desktop user may mount media. Native Koronos VFS drivers and block-device integration are still required before this is a native-kernel mount implementation.

## Linux directory hierarchy

fhs-layout.json describes a merged-/usr FHS-compatible root. create-fhs-tree.py --root <staging-root> creates the directory skeleton inside an explicit image root, preserves existing non-empty legacy directories, and normalizes standard /var/run and /var/lock links. It never writes to the host root by default. /proc, /sys, /dev, /run and /tmp are mount points; the script does not mount them.
