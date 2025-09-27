"""Generate a Shields.io-compatible badge for the supported Python version.

This script reads the `requires-python` field from `pyproject.toml` and
emits a JSON payload consumable by the Shields.io `endpoint` badge type.

Example usage::

    python scripts/generate_python_badge.py \
        --pyproject pyproject.toml \
        --output python-badge.json

The resulting JSON can be referenced in the README like::

    https://img.shields.io/endpoint?url=<RAW_JSON_URL>

The implementation intentionally avoids third-party dependencies so it can
run in minimal CI environments.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import tomllib

DEFAULT_PYPROJECT = Path("pyproject.toml")
DEFAULT_OUTPUT = Path("python-badge.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Python version badge JSON")
    parser.add_argument(
        "--pyproject",
        "-p",
        type=Path,
        default=DEFAULT_PYPROJECT,
        help="Path to pyproject.toml (default: pyproject.toml)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to write Shields.io endpoint JSON (default: python-badge.json)",
    )
    parser.add_argument(
        "--label",
        "-l",
        default="python",
        help="Badge label text (default: python)",
    )
    return parser.parse_args()


def load_requires_python(pyproject_path: Path) -> str:
    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found: {pyproject_path}")

    with pyproject_path.open("rb") as handle:
        data = tomllib.load(handle)

    try:
        requires = data["project"]["requires-python"]
    except KeyError as exc:
        raise KeyError("`project.requires-python` missing in pyproject.toml") from exc

    if not isinstance(requires, str) or not requires.strip():
        raise ValueError("`project.requires-python` must be a non-empty string")

    return requires.strip()


def humanize_specifier(spec: str) -> str:
    parts = [segment.strip() for segment in spec.split(",") if segment.strip()]

    equals = [segment[2:] for segment in parts if segment.startswith("==")]
    if equals:
        return equals[0]

    minimums: list[str] = []
    uppers: list[str] = []

    for segment in parts:
        if segment.startswith(">="):
            minimums.append(segment[2:])
        elif segment.startswith(">"):
            minimums.append(segment[1:])
        elif segment.startswith("<=") or segment.startswith("<"):
            # Normalise to strip leading comparison characters.
            uppers.append(segment.lstrip("<="))

    message: str
    if minimums:
        # Use the highest lower-bound to be safest.
        minimums.sort()
        message = f"{minimums[-1]}+"
    else:
        message = spec

    if uppers:
        uppers.sort()
        message = f"{message} <{uppers[0]}"

    return message


def write_badge_json(path: Path, label: str, message: str) -> None:
    payload = {
        "schemaVersion": 1,
        "label": label,
        "message": message,
        "color": "blue",
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def main() -> int:
    args = parse_args()

    try:
        spec = load_requires_python(args.pyproject)
    except (FileNotFoundError, KeyError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    message = humanize_specifier(spec)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_badge_json(args.output, args.label, message)

    print(
        f"Python badge generated: {args.output} -> {message}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
