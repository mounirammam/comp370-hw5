#!/usr/bin/env python3
"""Count NYC 311 complaints of each type per borough over a creation-date range.

Output is CSV with the columns: complaint type, borough, count
"""
import argparse
import csv
import sys
from collections import Counter
from datetime import datetime

CREATED_COL = 'Created Date'
TYPE_COL = 'Complaint Type'
BOROUGH_COL = 'Borough'

DATE_FORMATS = ('%Y-%m-%d', '%m/%d/%Y')


def parse_date_arg(text):
    """argparse type: accept YYYY-MM-DD or MM/DD/YYYY, return an int YYYYMMDD key."""
    for fmt in DATE_FORMATS:
        try:
            d = datetime.strptime(text, fmt)
            return d.year * 10000 + d.month * 100 + d.day
        except ValueError:
            pass
    raise argparse.ArgumentTypeError(
        f"invalid date '{text}' (expected YYYY-MM-DD or MM/DD/YYYY)")


def created_key(created):
    """'MM/DD/YYYY hh:mm:ss AM' -> int YYYYMMDD, or None if malformed."""
    try:
        return int(created[6:10]) * 10000 + int(created[0:2]) * 100 + int(created[3:5])
    except ValueError:
        return None


def count_complaints(infile, start, end):
    """Stream the CSV line by line (no pandas) and count (complaint type, borough)."""
    counts = Counter()
    reader = csv.reader(infile)
    header = next(reader)
    try:
        i_created = header.index(CREATED_COL)
        i_type = header.index(TYPE_COL)
        i_borough = header.index(BOROUGH_COL)
    except ValueError as e:
        sys.exit(f'error: input file is missing a required column ({e})')
    n_cols = max(i_created, i_type, i_borough)

    for row in reader:
        if len(row) <= n_cols:
            continue  # malformed / truncated row
        key = created_key(row[i_created])
        if key is None or not (start <= key <= end):
            continue
        borough = row[i_borough].strip().title() or 'Unspecified'
        counts[(row[i_type].strip(), borough)] += 1
    return counts


def write_counts(counts, out):
    writer = csv.writer(out, lineterminator='\n')
    writer.writerow(['complaint type', 'borough', 'count'])
    for (ctype, borough), n in sorted(counts.items(), key=lambda kv: (kv[0][0].lower(), kv[0][1])):
        writer.writerow([ctype, borough, n])


def main():
    parser = argparse.ArgumentParser(
        prog='borough_complaints.py',
        description='Output the number of each complaint type per borough for incidents '
                    'created within a given date range (inclusive), as CSV: '
                    'complaint type, borough, count.',
        epilog='example: borough_complaints.py -i nyc_311_2024.csv -s 2024-01-01 -e 2024-02-29 -o out.csv')
    parser.add_argument('-i', '--input', required=True, metavar='INPUT_CSV',
                        help='the input NYC 311 csv file')
    parser.add_argument('-s', '--start', required=True, type=parse_date_arg, metavar='START_DATE',
                        help='first creation date to include (YYYY-MM-DD or MM/DD/YYYY)')
    parser.add_argument('-e', '--end', required=True, type=parse_date_arg, metavar='END_DATE',
                        help='last creation date to include (YYYY-MM-DD or MM/DD/YYYY)')
    parser.add_argument('-o', '--output', metavar='OUTPUT_CSV',
                        help='write results to this file instead of stdout')
    args = parser.parse_args()

    if args.start > args.end:
        parser.error('start date must not be after end date')

    with open(args.input, newline='', encoding='utf-8', errors='replace') as f:
        counts = count_complaints(f, args.start, args.end)

    if args.output:
        with open(args.output, 'w', newline='', encoding='utf-8') as out:
            write_counts(counts, out)
    else:
        write_counts(counts, sys.stdout)


if __name__ == '__main__':
    main()
