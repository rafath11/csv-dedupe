# csv-dedupe

**The problem:** every CMDB and asset export has duplicates in it. The same row
exported twice, the same serial number living on two records — and every count
built on top of that file (device totals, license positions, refresh budgets)
is quietly wrong. People usually find out in a meeting, when two reports
disagree and nobody can say which one is lying.

**The fix:** check the file before the meeting does.

`csv-dedupe` is a single-file, zero-dependency Python script. It finds
duplicate rows in a CSV, shows you exactly where they are, and can write a
cleaned copy — without touching your original.

## Quick start

```bash
# report only — what duplicates are in this export?
python3 csv_dedupe.py export.csv

# also write export.clean.csv with duplicates removed
python3 csv_dedupe.py export.csv --write-clean

# dedupe by a key column instead of the whole row
# (catches the same serial number on two different records)
python3 csv_dedupe.py export.csv --key serial_number --write-clean
```

Example output:

```
File:        sample_assets.csv
Data rows:   5
Match mode:  key (serial_number)
Dup groups:  1
Dup rows:    2 (extra copies beyond the first)

Duplicates:
  rows 1, 3, 4: ('SN100',)
    ^ same key, 2 different row versions — check which is current
```

## Two kinds of duplicate, two modes

- **Exact mode (default):** a duplicate means every column is identical —
  safe to drop the extra copies.
- **Key mode (`--key`):** a duplicate means the key column(s) match, even if
  the rest of the row differs. That's the dangerous kind in asset data — one
  serial number, two records, different locations. csv-dedupe flags when the
  rows under one key disagree, because deleting either copy blindly can
  delete the truth.

## Options

| Flag | What it does |
|---|---|
| `--key COL[,COL]` | match on key column(s) instead of the whole row |
| `--keep first\|last` | which copy survives in the cleaned file (default: first) |
| `--write-clean` | write `<name>.clean.csv` with duplicates removed |
| `--delimiter` | field delimiter (default: `,`) |

## Exit codes (built for CI and cron)

- `0` — no duplicates found
- `1` — duplicates found
- `2` — usage or file error

MIT licensed. Python 3.8+, no dependencies.
