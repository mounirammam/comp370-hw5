# COMP 370/570 – Homework 5: NYC 311 data analysis

| File | Task |
|---|---|
| `conceptual_answers.md` | Conceptual questions 1–4 |
| `trim_2024.sh` | Trims the raw 311 CSV to 2024 incidents that have a zipcode, with **one** `grep` call |
| `borough_complaints.py` | Task 1 – CLI tool: complaint type × borough counts for a creation-date range |
| `task3_complaint_analysis.ipynb` | Task 3 – uses the CLI tool from Jupyter, makes the bar charts |
| `complaint_type_analysis.md` | Task 3 – write-up of what the analysis revealed |
| `bokeh_dashboard/preprocess.py` | Task 4 – pre-computes monthly average response times per zipcode |
| `bokeh_dashboard/main.py` | Task 4 – Bokeh server dashboard |

Data is **not** committed (see `.gitignore`).

## 0. Get and trim the data

```bash
# raw file from MyCourses: a .tar.gz containing 311_Service_Requests_from_2010_to_Present_20250928.csv (6.8 GB)
mkdir -p ~/hw5_data
tar -xzOf 311_records.csv.tgz 311_Service_Requests_from_2010_to_Present_20250928.csv \
  | ./trim_2024.sh /dev/stdin ~/hw5_data/nyc_311_2024.csv
```

The single grep keeps the header plus every row whose `Created Date` (field 2) is in 2024 and whose
`Incident Zip` (field 9) starts with 5 digits. Quoted fields with commas in fields 4–8 are handled by the regex.

## 1. CLI tool

```bash
python borough_complaints.py -h
python borough_complaints.py -i ~/hw5_data/nyc_311_2024.csv -s 2024-01-01 -e 2024-02-29            # stdout
python borough_complaints.py -i ~/hw5_data/nyc_311_2024.csv -s 2024-01-01 -e 2024-02-29 -o out.csv
```

Dates are inclusive and may be given as `YYYY-MM-DD` or `MM/DD/YYYY`. The file is streamed line by line
with the `csv` module (no pandas), so memory use stays flat.

## 2. Jupyter on EC2

```bash
pip install -r requirements.txt
jupyter notebook --no-browser --port 8888          # on the EC2
ssh -i EC2Key.pem -L 8888:localhost:8888 ubuntu@<EC2 public DNS>   # on your laptop, then open http://localhost:8888
```

## 3. Notebook

Open `task3_complaint_analysis.ipynb` and run all cells (set `NYC311_2024` if the data isn't at `~/hw5_data/nyc_311_2024.csv`).

## 4. Dashboard

```bash
python bokeh_dashboard/preprocess.py -i ~/hw5_data/nyc_311_2024.csv   # writes bokeh_dashboard/data/monthly_response_times.csv
bokeh serve --show bokeh_dashboard                                   # local
# on EC2 (open port 8080 in the security group):
bokeh serve bokeh_dashboard --port 8080 --allow-websocket-origin=<EC2 public DNS>:8080
```

Design decisions (following the assignment FAQ):
- incidents are included if they were **created** in 2024
- response time = closed − created, in **hours**
- incidents with no closed date, a closed date before the created date, or no valid zipcode are dropped
- an incident counts toward the month it was **closed**; the plot shows January–December 2024
  (incidents created in 2024 but closed in 2025 are kept in the pre-processed table but fall outside the plotted range)
- side effect of these two rules: early-2024 months look faster than they are, because e.g. January closures can only
  come from incidents opened in January (slow incidents opened in late 2023 are excluded)
- the assignment text says "ALL 2020 data", which is a typo for 2024 (the dataset in use is 2024)

The dashboard only loads ~3k pre-computed averages, so a dropdown change is a lookup and redraws immediately (well below the 5-second requirement).

## Submission bundle

```bash
./make_submission.sh   # builds submission/ with complaint_borough.py, complaint_type_analysis.md, Bokeh.tgz
```
