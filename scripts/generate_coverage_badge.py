"""Generate a Shields.io-compatible coverage badge JSON from coverage.xml.

This script reads a Coverage.py XML report (typically generated via pytest-cov)
and emits a JSON file consumable by the Shields.io `endpoint` badge type.

Example usage::

    python scripts/generate_coverage_badge.py \
        --input test-results/coverage.xml \
        --output coverage-badge.json

The resulting JSON can be referenced from a README badge like:

    https://img.shields.io/endpoint?url=<RAW_JSON_URL>

The script is lightweight and dependency-free to make it easy to run in CI.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

DEFAULT_INPUT = Path("test-results/coverage.xml")
DEFAULT_OUTPUT = Path("coverage-badge.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate coverage badge JSON")
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=DEFAULT_INPUT,
        help="Path to coverage XML (default: test-results/coverage.xml)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to write Shields.io endpoint JSON (default: coverage-badge.json)",
    )
    parser.add_argument(
        "--label",
        "-l",
        default="coverage",
        help="Badge label text (default: coverage)",
    )
    parser.add_argument(
        "--precision",
        "-p",
        type=int,
        default=1,
        help="Number of decimal places to include in percentage (default: 1)",
    )
    return parser.parse_args()


def load_coverage_percentage(xml_path: Path) -> float:
    if not xml_path.exists():
        raise FileNotFoundError(f"Coverage XML not found: {xml_path}")

    root = ET.parse(xml_path).getroot()
    line_rate = root.get("line-rate")
    if line_rate is None:
        raise ValueError("`line-rate` attribute missing in coverage XML root element")

    try:
        return float(line_rate) * 100
    except ValueError as exc:
        raise ValueError(f"Invalid line-rate value: {line_rate}") from exc


def pick_color(percentage: float) -> str:
    if percentage >= 90:
        return "green"
    if percentage >= 80:
        return "yellowgreen"
    if percentage >= 65:
        return "yellow"
    if percentage >= 50:
        return "orange"
    return "red"


def format_message(percentage: float, precision: int) -> str:
    quantized = round(percentage, precision)
    if precision == 0:
        return f"{int(quantized)}%"
    return f"{quantized:.{precision}f}%"


def write_badge_json(path: Path, label: str, message: str, color: str) -> None:
    payload = {
        "schemaVersion": 1,
        "label": label,
        "message": message,
        "color": color,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def main() -> int:
    args = parse_args()

    try:
        percentage = load_coverage_percentage(args.input)
    except (FileNotFoundError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    message = format_message(percentage, args.precision)
    color = pick_color(percentage)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_badge_json(args.output, args.label, message, color)

    print(
        f"Coverage badge generated: {args.output} -> {message} ({color})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
