#!/usr/bin/env python3
"""Review data files named from the first column of an Excel workbook.

For each non-empty name in column A, constructs ``prefix + name + suffix``,
opens it with the supplied plotting script, and asks for a quality rating.
Ratings are written to a copy of the workbook in the same row order.

Example:
    python rate_data_quality.py samples.xlsx \
        --prefix '/data/run_' --suffix '.csv' \
        --plot-script plot_data.py --output ratings.xlsx

The plotting script is run as ``python plot_data.py DATA_FILE`` by default.
Use --plot-command to specify a different command; include ``{file}`` where
the data-file path should be inserted, e.g. --plot-command 'python {file}'
is usually not useful, while --plot-command 'my_viewer --input {file}' is.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path

from openpyxl import load_workbook


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path, help="Input .xlsx workbook")
    parser.add_argument("--prefix", default="", help="Path/name prefix")
    parser.add_argument("--suffix", default="", help="Filename suffix, e.g. .csv")
    parser.add_argument("--sheet", help="Worksheet name (default: active sheet)")
    parser.add_argument("--plot-command", help="Command template containing {file}")
    parser.add_argument("--output", type=Path, help="Output workbook (default: <input>_ratings.xlsx)")
    parser.add_argument("--rating-header", default="QCRating")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.workbook.is_file():
        raise SystemExit(f"Workbook not found: {args.workbook}")
    if not args.plot_command:
        raise SystemExit("Provide --plot-command.")

    workbook = load_workbook(args.workbook)
    if args.sheet:
        if args.sheet not in workbook.sheetnames:
            raise SystemExit(f"Worksheet not found: {args.sheet}")
        sheet = workbook[args.sheet]
    else:
        sheet = workbook.active

    # Add ratings in the next column, preserving every source row and its order.
    rating_col = sheet.max_column + 1
    sheet.cell(row=1, column=rating_col, value=args.rating_header)
    for row in range(2, sheet.max_row + 1):
        name = sheet.cell(row=row, column=7).value
        if name is None or str(name).strip() == "":
            continue

        year = name.split("_")[1]
        data_file = Path(f"{args.prefix}/{year}/{str(name).strip()}{args.suffix}")
      
        print(f"\nRow {row}: {name} -> {data_file}")
        if not data_file.is_file():
            print("File not found. Rating this row as missing.")
            rating = None
        else:
            if args.plot_command:
                command = [part.replace("{file}", str(data_file))
                           for part in shlex.split(args.plot_command)]
            try:
                plot_process = subprocess.Popen(command)
            except OSError as exc:
                raise SystemExit(f"Could not launch plot command {command!r}: {exc}")
            
            try:
                while True:
                    try:
                        rating = input("Rate data quality (0 = bad, 1 = good): ").strip()
                    except EOFError:
                        print("\nInput ended; leaving remaining ratings blank.")
                        rating = ""
                        break
                    if rating in {"0", "1"}:
                        rating = int(rating)
                        break
                    print("Please enter a rating, 0 for bad, 1 for good, or Ctrl-D to leave it blank.")
            finally:
                if plot_process.poll() is None:
                    plot_process.terminate()
                    try:
                        plot_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        print("Plotting process did not terminate; killing it.")
                        plot_process.kill()
                        plot_process.wait()

        sheet.cell(row=row, column=rating_col, value=rating)

    output = args.output or args.workbook.with_name(f"{args.workbook.stem}_ratings.xlsx")
    workbook.save(output)
    print(f"Saved ratings to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
