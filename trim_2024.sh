#!/usr/bin/env bash
# Trim the raw NYC 311 CSV down to incidents created in 2024 that have a zipcode,
# using exactly ONE call to grep.
#
#   usage: ./trim_2024.sh <raw 311 csv> <output csv>
#   e.g.   ./trim_2024.sh 311_Service_Requests_from_2010_to_Present_20250928.csv nyc_311_2024.csv
#
# Pattern 1 keeps the header line.
# Pattern 2 keeps a row when
#   - field 2 (Created Date, MM/DD/YYYY hh:mm:ss AM) is in 2024, and
#   - field 9 (Incident Zip) starts with 5 digits.
# Fields 4-8 (Agency, Agency Name, Complaint Type, Descriptor, Location Type) can be
# quoted and contain commas, so each is matched as  ("...")+  or a plain comma-free value.
set -euo pipefail

F='(("[^"]*")+|[^,"]*)'
LC_ALL=C grep -E \
    -e '^Unique Key,' \
    -e "^[0-9]+,[0-9]{2}/[0-9]{2}/2024 [^,]*,[^,]*,$F,$F,$F,$F,$F,[0-9]{5}[,-]" \
    "$1" > "$2"
