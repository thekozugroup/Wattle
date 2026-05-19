#!/usr/bin/env python3
"""Build a self-extracting dist/Wattle.skill installer."""

from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import io
import tarfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "wattle"
DIST_DIR = ROOT / "dist"
DEFAULT_OUT = DIST_DIR / "Wattle.skill"
EXCLUDED_PARTS = {"__pycache__", ".DS_Store"}


def iter_payload_files() -> list[Path]:
    files: list[Path] = []
    for path in SKILL_DIR.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_payload_tar() -> bytes:
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) as tf:
            for path in iter_payload_files():
                rel = path.relative_to(SKILL_DIR)
                info = tarfile.TarInfo(f"wattle/{rel.as_posix()}")
                data = path.read_bytes()
                info.size = len(data)
                info.mtime = 1767225600
                info.mode = 0o755 if path.name == "wattle.py" else 0o644
                info.uid = 0
                info.gid = 0
                info.uname = ""
                info.gname = ""
                tf.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def installer_script(payload: bytes) -> str:
    encoded = base64.b64encode(payload).decode("ascii")
    wrapped = "\n".join(textwrap.wrap(encoded, width=76))
    return f"""#!/usr/bin/env bash
set -euo pipefail

usage() {{
  cat <<'USAGE'
Wattle.skill single-file installer

Usage:
  bash Wattle.skill --install          Install globally for Codex via npx skills
  bash Wattle.skill --install-project  Install into current project via npx skills
  bash Wattle.skill --extract DIR      Extract payload to DIR
  bash Wattle.skill --help             Show this help
USAGE
}}

extract_payload() {{
  local dest="$1"
  mkdir -p "$dest"
  local tmp
  tmp="$(mktemp)"
  local self="${{BASH_SOURCE[0]:-$0}}"
  awk '/^__WATTLE_PAYLOAD_BELOW__$/ {{ found=1; next }} found {{ print }}' "$self" | base64 -d > "$tmp"
  tar -xzf "$tmp" -C "$dest"
  rm -f "$tmp"
}}

case "${{1:---help}}" in
  --extract)
    if [ "${{2:-}}" = "" ]; then
      echo "missing extract destination" >&2
      exit 2
    fi
    extract_payload "$2"
    echo "Extracted Wattle to $2/wattle"
    ;;
  --install)
    tmpdir="$(mktemp -d)"
    extract_payload "$tmpdir"
    npx skills add "$tmpdir/wattle" -g -a codex --copy -y
    rm -rf "$tmpdir"
    ;;
  --install-project)
    tmpdir="$(mktemp -d)"
    extract_payload "$tmpdir"
    npx skills add "$tmpdir/wattle" -a codex --copy -y
    rm -rf "$tmpdir"
    ;;
  --help|-h)
    usage
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
exit 0
__WATTLE_PAYLOAD_BELOW__
{wrapped}
"""


def build_bundle(out: Path = DEFAULT_OUT) -> dict:
    if not (SKILL_DIR / "SKILL.md").exists():
        raise FileNotFoundError("wattle/SKILL.md is required")
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()

    files = iter_payload_files()
    payload = build_payload_tar()
    out.write_text(installer_script(payload), encoding="utf-8")
    out.chmod(0o755)

    manifest = {
        "bundle": str(out.relative_to(ROOT)),
        "sha256": sha256(out),
        "payload_sha256": sha256_bytes(payload),
        "file_count": len(files),
        "payload_root": "wattle",
        "install_hint": f"bash {out.relative_to(ROOT)} --install",
    }
    (out.with_suffix(out.suffix + ".json")).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Wattle.skill release bundle")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output .skill file")
    args = parser.parse_args()
    manifest = build_bundle(Path(args.out))
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
