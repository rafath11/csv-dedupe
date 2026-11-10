#!/usr/bin/env python3
"""csv-dedupe — find and remove duplicate rows in a CSV export.

Built for the exports practitioners actually fight with: CMDB dumps, asset
registers, license lists — files where the same row shows up twice (or the
same asset shows up under two rows) and every count downstream is wrong.

Zero dependencies. Python 3.8+.

Modes:
  exact (default)  duplicate = every column identical
  --key COL[,COL]  duplicate = same value in the key column(s), even if
                   other columns differ (reports the conflicts it finds)

Usage:
  python3 csv_dedupe.py export.csv                      # report only
  python3 csv_dedupe.py export.csv --write-clean        # + cleaned file
  python3 csv_dedupe.py export.csv --key serial_number  # dedupe by key
  python3 csv_dedupe.py export.csv --keep last          # keep last copy

Exit codes: 0 = no duplicates, 1 = duplicates found, 2 = usage/file error.
"""
import argparse
import csv
import sys
from collections import OrderedDict


def fingerprint(row, key_idx):
    if key_idx is None:
        return tuple(row)
    return tuple(row[i] for i in key_idx)


def main(argv=None):
    p = argparse.ArgumentParser(description="Find/remove duplicate rows in a CSV.")
    p.add_argument("file", help="CSV file to check")
    p.add_argument("--key", help="comma-separated key column name(s) instead of whole-row match")
    p.add_argument("--keep", choices=["first", "last"], default="first",
                   help="which copy of a duplicate to keep (default: first)")
    p.add_argument("--write-clean", action="store_true",
                   help="write <name>.clean.csv with duplicates removed")
    p.add_argument("--delimiter", default=",", help="field delimiter (default: ,)")
    args = p.parse_args(argv)

    try:
        with open(args.file, newline="", encoding="utf-8-sig") as fh:
            rows = list(csv.reader(fh, delimiter=args.delimiter))
    except OSError as e:
        print(f"ERROR: cannot read {args.file}: {e}", file=sys.stderr)
        return 2
    if not rows:
        print("ERROR: file is empty", file=sys.stderr)
        return 2

    header, data = rows[0], rows[1:]
    key_idx = None
    if args.key:
        cols = [c.strip() for c in args.key.split(",")]
        missing = [c for c in cols if c not in header]
        if missing:
            print(f"ERROR: key column(s) not in header: {', '.join(missing)}", file=sys.stderr)
            print(f"Header is: {', '.join(header)}", file=sys.stderr)
            return 2
        key_idx = [header.index(c) for c in cols]

    groups = OrderedDict()  # fingerprint -> [row numbers (1-based, data rows)]
    for n, row in enumerate(data, start=1):
        groups.setdefault(fingerprint(row, key_idx), []).append(n)

    dup_groups = {k: v for k, v in groups.items() if len(v) > 1}
    dup_rows = sum(len(v) - 1 for v in dup_groups.values())

    label = f"key ({args.key})" if args.key else "exact row"
    print(f"File:        {args.file}")
    print(f"Data rows:   {len(data)}")
    print(f"Match mode:  {label}")
    print(f"Dup groups:  {len(dup_groups)}")
    print(f"Dup rows:    {dup_rows} (extra copies beyond the first)")

    if dup_groups:
        print("\nDuplicates:")
        for fp, nums in dup_groups.items():
            shown = fp if len(str(fp)) <= 110 else str(fp)[:107] + "..."
            print(f"  rows {', '.join(map(str, nums))}: {shown}")
            if key_idx is not None and len(nums) > 1:
                variants = {tuple(data[n - 1]) for n in nums}
                if len(variants) > 1:
                    print(f"    ^ same key, {len(variants)} different row versions — check which is current")

    if args.write_clean:
        keep_idx = set()
        for fp, nums in groups.items():
            keep_idx.add(nums[0] if args.keep == "first" else nums[-1])
        out_name = args.file.rsplit(".csv", 1)[0] + ".clean.csv"
        with open(out_name, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh, delimiter=args.delimiter)
            w.writerow(header)
            for n, row in enumerate(data, start=1):
                if n in keep_idx:
                    w.writerow(row)
        print(f"\nCleaned file written: {out_name} ({len(keep_idx)} rows kept)")

    return 1 if dup_groups else 0


if __name__ == "__main__":
    sys.exit(main())
