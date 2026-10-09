#!/usr/bin/env bash
# Build the files to upload to MyCourses.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p submission
cp borough_complaints.py submission/complaint_borough.py
cp complaint_type_analysis.md submission/
# Bokeh.tgz: source code only (no data, no caches)
tar -czf submission/Bokeh.tgz --exclude='data' --exclude='__pycache__' bokeh_dashboard/preprocess.py bokeh_dashboard/main.py
tar -tzf submission/Bokeh.tgz
ls -la submission
