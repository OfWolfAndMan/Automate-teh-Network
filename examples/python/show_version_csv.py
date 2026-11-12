"""Parse `show version` captures into a hardware inventory CSV, with ntc-templates.

Lesson: never regex a show command someone else has already written a parser for.
ntc-templates is a library of TextFSM templates for hundreds of commands; `parse_output`
turns screen text into a list of dictionaries, and `csv.DictWriter` turns those into a file
a spreadsheet can open.

Modernised from the mini-course's inventory/inventory_parser.py, which ran on import,
wrote to an `outputs/` directory that did not exist, leaked an open file handle per input,
and dropped list-valued fields (a stack has one serial per member) on the floor.

Runs offline against the repository's fixtures:

    python examples/python/show_version_csv.py tests/fixtures/show/*_show_version.txt
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import TextIO

FIELDS = ["hostname", "version", "hardware", "serial", "uptime", "running_image"]


def parse_show_version(text: str, platform: str = "cisco_ios") -> dict[str, str]:
    from ntc_templates.parse import parse_output

    [record] = parse_output(platform=platform, command="show version", data=text)
    # A switch stack reports one hardware model and serial per member: keep them all.
    return {k: " ".join(v) if isinstance(v, list) else v
            for k, v in record.items() if k in FIELDS}


def write_csv(rows: list[dict[str, str]], out: TextIO) -> None:
    writer = csv.DictWriter(out, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("captures", nargs="+", type=Path)
    ap.add_argument("--platform", default="cisco_ios")
    ap.add_argument("-o", "--output", type=Path, help="CSV file (default: stdout)")
    a = ap.parse_args()

    rows = [parse_show_version(p.read_text(), a.platform) for p in a.captures]
    if a.output:
        with a.output.open("w", newline="") as fh:
            write_csv(rows, fh)
    else:
        write_csv(rows, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
