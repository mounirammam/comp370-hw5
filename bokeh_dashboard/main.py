"""NYC 311 response-time dashboard (Bokeh server app).

Run (from the repo root):
    python bokeh_dashboard/preprocess.py -i <trimmed 2024 csv>     # once, ~1-2 min
    bokeh serve --show bokeh_dashboard                               # local
    bokeh serve bokeh_dashboard --port 8080 --allow-websocket-origin=<EC2 public DNS>:8080   # EC2

All heavy lifting is done by preprocess.py; this app only loads the small table of
monthly averages, so every dropdown change is a dictionary lookup (well under 5 s).
"""
import csv
import os
from collections import defaultdict
from datetime import datetime

from bokeh.io import curdoc
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, HoverTool, Select
from bokeh.plotting import figure

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'monthly_response_times.csv')

# Incidents are assigned to the month they were closed; we plot the 12 months of 2024.
MONTHS = [f'2024-{m:02d}' for m in range(1, 13)]
MONTH_DATES = [datetime(2024, m, 1) for m in range(1, 13)]


def load_averages(path):
    """-> {zipcode: {'YYYY-MM': avg_hours}}, plus each zipcode's incident count in 2024."""
    avgs = defaultdict(dict)
    totals = defaultdict(int)
    with open(path, newline='') as f:
        for r in csv.DictReader(f):
            avgs[r['zipcode']][r['month']] = float(r['avg_hours'])
            if r['month'] in MONTHS:
                totals[r['zipcode']] += int(r['n'])
    return avgs, totals


AVGS, TOTALS = load_averages(DATA_FILE)
ZIPCODES = sorted(z for z in AVGS if z != 'ALL' and TOTALS[z] > 0)
# default to the two zipcodes with the most closed 2024 incidents
DEFAULT_1, DEFAULT_2 = sorted(ZIPCODES, key=lambda z: -TOTALS[z])[:2]


def series(zipcode):
    by_month = AVGS.get(zipcode, {})
    return [by_month.get(m, float('nan')) for m in MONTHS]  # NaN -> gap in the line


source = ColumnDataSource(data=dict(month=MONTH_DATES, all=series('ALL'),
                                    zip1=series(DEFAULT_1), zip2=series(DEFAULT_2)))

options = [(z, f'{z}  ({TOTALS[z]:,} incidents)') for z in ZIPCODES]
select1 = Select(title='Zipcode 1', value=DEFAULT_1, options=options, width=300)
select2 = Select(title='Zipcode 2', value=DEFAULT_2, options=options, width=300)

p = figure(title='Monthly average 311 response time (incident created → closed), 2024',
           x_axis_type='datetime', width=900, height=450,
           x_axis_label='Month incident was closed (2024)',
           y_axis_label='Average response time (hours)',
           tools='pan,box_zoom,wheel_zoom,reset,save')
p.xaxis.formatter.months = '%b %Y'
p.y_range.start = 0

p.ygrid.grid_line_alpha = 0.4
p.xgrid.grid_line_color = None

curves = [('all', 'All zipcodes', '#52514e', 'dashed'),
          ('zip1', f'Zipcode 1: {DEFAULT_1}', '#2a78d6', 'solid'),
          ('zip2', f'Zipcode 2: {DEFAULT_2}', '#eb6834', 'solid')]
for col, label, color, dash in curves:
    p.line('month', col, source=source, line_width=2, color=color, line_dash=dash, legend_label=label)
    p.scatter('month', col, source=source, size=8, color=color, line_color='white',
              line_width=2, legend_label=label)

p.add_tools(HoverTool(tooltips=[('month', '@month{%b %Y}'), ('all zipcodes', '@all{0.0} h'),
                                ('zipcode 1', '@zip1{0.0} h'), ('zipcode 2', '@zip2{0.0} h')],
                      formatters={'@month': 'datetime'}, mode='vline'))
p.legend.location = 'top_left'
p.legend.click_policy = 'hide'
legend_items = {item.label['value']: item for item in p.legend.items}
item1 = legend_items[curves[1][1]]
item2 = legend_items[curves[2][1]]


def update(attr, old, new):
    z1, z2 = select1.value, select2.value
    source.data = dict(month=MONTH_DATES, all=series('ALL'), zip1=series(z1), zip2=series(z2))
    item1.label = dict(value=f'Zipcode 1: {z1}')
    item2.label = dict(value=f'Zipcode 2: {z2}')


select1.on_change('value', update)
select2.on_change('value', update)

curdoc().add_root(column(select1, select2, p))
curdoc().title = 'NYC 311 response time by zipcode'
