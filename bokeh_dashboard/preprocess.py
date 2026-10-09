#!/usr/bin/env python3
"""Pre-compute monthly average 311 response times (create -> close, in hours) per zipcode.

Reads the trimmed 2024 NYC 311 csv line by line (no pandas, so memory stays flat) and
writes a small csv the dashboard can load instantly:

    zipcode,month,avg_hours,n
    ALL,2024-01,52.31,250123
    10001,2024-01,40.12,1234
    ...

Rules (from the assignment FAQ):
  - only incidents CREATED in 2024
  - drop incidents without a closed date (not closed yet)
  - drop incidents without a valid 5-digit zipcode
  - drop incidents whose closed date is before their created date (negative response time)
  - an incident belongs to the month in which it was CLOSED

usage: python preprocess.py -i nyc_311_2024.csv [-o data/monthly_response_times.csv]
"""
import argparse
import csv
import os
from collections import defaultdict
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(HERE, 'data', 'monthly_response_times.csv')


def parse_ts(s):
    """Fast parse of 'MM/DD/YYYY hh:mm:ss AM' -> datetime (None if malformed)."""
    try:
        hour = int(s[11:13]) % 12
        if s[20:22] == 'PM':
            hour += 12
        return datetime(int(s[6:10]), int(s[0:2]), int(s[3:5]),
                        hour, int(s[14:16]), int(s[17:19]))
    except (ValueError, IndexError):
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('-i', '--input', required=True, help='trimmed 2024 NYC 311 csv')
    parser.add_argument('-o', '--output', default=DEFAULT_OUT, help='output csv (default: %(default)s)')
    args = parser.parse_args()

    # (zipcode, 'YYYY-MM') -> [sum_hours, count]; zipcode 'ALL' holds the citywide totals
    acc = defaultdict(lambda: [0.0, 0])
    stats = defaultdict(int)

    with open(args.input, newline='', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f)
        header = next(reader)
        i_created = header.index('Created Date')
        i_closed = header.index('Closed Date')
        i_zip = header.index('Incident Zip')
        n_cols = max(i_created, i_closed, i_zip)

        for row in reader:
            stats['rows'] += 1
            if len(row) <= n_cols:
                stats['malformed'] += 1
                continue
            created = parse_ts(row[i_created])
            if created is None or created.year != 2024:
                stats['not_2024'] += 1
                continue
            zipcode = row[i_zip].strip()[:5]
            if len(zipcode) != 5 or not zipcode.isdigit():
                stats['no_zip'] += 1
                continue
            closed = parse_ts(row[i_closed])
            if closed is None:
                stats['not_closed'] += 1
                continue
            hours = (closed - created).total_seconds() / 3600.0
            if hours < 0:
                stats['negative'] += 1
                continue

            month = f'{closed.year}-{closed.month:02d}'
            for key in ((zipcode, month), ('ALL', month)):
                a = acc[key]
                a[0] += hours
                a[1] += 1
            stats['kept'] += 1

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, 'w', newline='', encoding='utf-8') as out:
        w = csv.writer(out)
        w.writerow(['zipcode', 'month', 'avg_hours', 'n'])
        for (zipcode, month), (total, n) in sorted(acc.items()):
            w.writerow([zipcode, month, f'{total / n:.4f}', n])

    for k in ('rows', 'kept', 'not_closed', 'negative', 'no_zip', 'not_2024', 'malformed'):
        print(f'{k:>11}: {stats[k]:,}')
    print(f'wrote {len(acc):,} (zipcode, month) averages to {args.output}')


if __name__ == '__main__':
    main()
