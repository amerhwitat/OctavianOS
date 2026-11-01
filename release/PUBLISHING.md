# Publishing this release to GitHub

The ISO was built and verified locally. Publishing a GitHub Release requires a
token with `contents: write` for `amerhwitat/OctavianOS`; no credentials are
available inside this sandbox, so the release is staged here for upload.

## Artifacts

| File | Size | SHA-256 |
|---|---|---|
| `OctavianOS-ChimeraII-1.0.0-amd64.iso` | 900,200,448 bytes | `65be61d3aeddcae155b2b1463de1291ab38901269618ae14fd9f86a1b253d523` |
| `OctavianOS-ChimeraII-0.1.0-amd64.iso` | 127,852,544 bytes | `0aa1f42471615dcaa5571c98b255916db1a489405a57ebe4523b187d442868f3` |

## Option A — GitHub CLI (recommended)

```sh
cd /workspace/OctavianOS
gh auth login                       # or: export GH_TOKEN=<token>
gh release create v1.0.0 \
  release/OctavianOS-ChimeraII-1.0.0-amd64.iso \
  release/SHA256SUMS \
  release/RELEASE-NOTES.md \
  --repo amerhwitat/OctavianOS \
  --title "OctavianOS 1.0.0 — complete bootable live app runtime" \
  --notes-file release/RELEASE-NOTES.md
```

## Option B — REST API

```sh
export GH_TOKEN=<token>
curl -sS -X POST \
  -H "Authorization: Bearer $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/amerhwitat/OctavianOS/releases \
  -d '{"tag_name":"v1.0.0","name":"OctavianOS 1.0.0 — complete bootable live app runtime","body":"See RELEASE-NOTES.md","draft":false,"prerelease":false}'
```

Then upload the asset to the returned `upload_url`:

```sh
curl -sS -X POST \
  -H "Authorization: Bearer $GH_TOKEN" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @release/OctavianOS-ChimeraII-1.0.0-amd64.iso \
  "<upload_url>?name=OctavianOS-ChimeraII-1.0.0-amd64.iso"
```

## Option C — commit the build fixes first

The fixes live in the vendored source tree. Before tagging, commit and push:

```sh
cd /workspace/OctavianOS
git add -A
git commit -m "Ship 1.0.0 live app-runtime ISO: Docker-free rootfs, systemd init, live-boot fix, kernel staging, coreutils preservation"
git push origin HEAD
```

## Verify after download

```sh
sha256sum -c SHA256SUMS
```
