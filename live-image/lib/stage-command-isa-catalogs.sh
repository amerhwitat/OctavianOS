#!/usr/bin/env bash
set -Eeuo pipefail
VENDOR="${1:?usage: stage-command-isa-catalogs.sh VENDORED_CHIMERA_SOURCE PAYLOAD_ROOT}"
PAYLOAD="${2:?usage: stage-command-isa-catalogs.sh VENDORED_CHIMERA_SOURCE PAYLOAD_ROOT}"
[[ -d "$VENDOR" && -d "$PAYLOAD" ]] || { echo "vendor source and payload must exist" >&2; exit 2; }
for rel in system/commands isa userland/commands tools/commands; do
  [[ -d "$VENDOR/$rel" ]] || { echo "missing catalogue source directory: $rel" >&2; exit 2; }
  mkdir -p "$PAYLOAD/$rel"
  cp -a "$VENDOR/$rel/." "$PAYLOAD/$rel/"
done
[[ -s "$VENDOR/ISA.csv" ]] || { echo "missing ISA.csv" >&2; exit 2; }
install -D -m 0644 "$VENDOR/ISA.csv" "$PAYLOAD/ISA.csv"
[[ -s "$VENDOR/UPSTREAM_REVISION" ]] || { echo "missing upstream revision provenance" >&2; exit 2; }
mkdir -p "$PAYLOAD/catalog-provenance"
install -m 0644 "$VENDOR/UPSTREAM_REVISION" "$PAYLOAD/catalog-provenance/UPSTREAM_REVISION"
(
  cd "$PAYLOAD"
  find system/commands isa userland/commands tools/commands -type f -print0 | sort -z | xargs -0 sha256sum
  sha256sum ISA.csv catalog-provenance/UPSTREAM_REVISION
) > "$PAYLOAD/catalog-provenance/command-isa.SHA256SUMS"
python3 - "$PAYLOAD" <<'PY'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
files = [*root.glob("system/commands/**/*.json"), *root.glob("isa/**/*.json"),
         *root.glob("userland/commands/**/*.json"), *root.glob("tools/commands/**/*.json")]
for path in files:
    json.loads(path.read_text(encoding="utf-8"))
manifest = {
    "schema": "octavian-command-isa-catalogues/v1",
    "source_revision": (root / "catalog-provenance/UPSTREAM_REVISION").read_text().strip(),
    "json_catalogue_count": len(files),
    "catalogue_roots": ["system/commands", "isa", "userland/commands", "tools/commands"],
    "isa_csv": "ISA.csv",
    "binary_status": "catalogue-data-only; entries are not claimed as implemented executables or tested ISA backends",
}
(root / "catalog-provenance/command-isa-manifest.json").write_text(
    json.dumps(manifest, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
print("staged and JSON-validated command/ISA catalogue files:", len(files))
PY
