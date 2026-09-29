#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import csv
import mimetypes
import re
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
ASSET_CSV = SKILL_DIR / "assets" / "images.csv"
OUTPUT_DIR = SCRIPT_DIR / "outputs"


def tokenize(text: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", text.lower()) if token}


def load_rows() -> list[dict[str, str]]:
    with ASSET_CSV.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def choose_best(description: str, rows: list[dict[str, str]]) -> dict[str, str]:
    description_tokens = tokenize(description)
    best_row = None
    best_score = -1

    for row in rows:
      tag_tokens = tokenize(row["tags"])
      score = len(description_tokens & tag_tokens)
      if score > best_score:
          best_score = score
          best_row = row

    if best_row is None:
        raise RuntimeError("No images were found in images.csv")

    return best_row


def decode_file(row: dict[str, str]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / row["filename"]
    output_path.write_bytes(base64.b64decode(row["image-base64"]))
    return output_path


def verify_file(path: Path) -> str:
    result = subprocess.run(
        ["file", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def infer_mime(path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(path.name)
    return mime_type or "application/octet-stream"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find the most relevant bundled image for a UI design prompt."
    )
    parser.add_argument("description", help="Description of the desired image context")
    args = parser.parse_args()

    if not ASSET_CSV.exists():
        print(f"Missing asset catalog: {ASSET_CSV}", file=sys.stderr)
        return 1

    rows = load_rows()
    chosen = choose_best(args.description, rows)
    output_path = decode_file(chosen)
    file_info = verify_file(output_path)
    mime_type = infer_mime(output_path)

    print(
        f"Matched image '{chosen['image-id']}' written to {output_path} "
        f"({mime_type}; {file_info})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
