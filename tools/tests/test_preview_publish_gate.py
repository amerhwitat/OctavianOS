#!/usr/bin/env python3
"""Fail closed if preview-container publication can bypass production DAPS."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/publish-octavianos-preview.yml"


def main() -> int:
    if not WORKFLOW.is_file():
        print("PREVIEW PUBLISH FAIL: workflow missing", file=sys.stderr)
        return 1
    text = WORKFLOW.read_text(encoding="utf-8")
    required = (
        "workflow_dispatch:",
        "evidence_run_id:",
        "evidence_artifact_name:",
        '[[ "$result" == "completed:success" ]]',
        "actions/download-artifact@v4",
        "python3 tools/release/verify-production-daps.py --evidence build/production-daps/evidence.json",
        "docker/login-action@v3",
        "docker/build-push-action@v6",
        "push: true",
    )
    for token in required:
        if token not in text:
            print(f"PREVIEW PUBLISH FAIL: missing gate contract: {token}", file=sys.stderr)
            return 1
    verifier = text.index("python3 tools/release/verify-production-daps.py --evidence")
    publish = text.index("docker/build-push-action@v6")
    if verifier >= publish:
        print("PREVIEW PUBLISH FAIL: container publication is ordered before DAPS verification", file=sys.stderr)
        return 1
    print("PREVIEW PUBLISH PASS: successful source run and production DAPS evidence are required before push")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
