from bokeh.models import Button, ColumnDataSource, Select, Slider
from bokeh.themes import built_in_themes
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.plotting import figure, show
from numpy.random import random, normal
import numpy as np
import pandas as pd
import sys
sys.path.append('src')
import options_load_mongoDB_dict as opt


# SOURCE
source = ColumnDataSource(data=dict(x=[], y=[], alpha = []))


# initial quotes bootstrap:
d = opt.db_lookup('SPY', start_date = opt.start_date, end_date = opt.end_date)
d.get_quotes_df()
quotes_df = d.quotes_df
quotes_df

def date_dict():
	date_dict = {}
	dates = quotes_df['datetime'].unique()
	dates = pd.Series(dates)
	dates_str = pd.to_datetime(dates, unit = 'ms')
	dates_str = dates_str.astype(str)
	for i in range(len(dates)):
		date_dict[dates_str[i]] = dates[i]
	return date_dict


available_dates = date_dict()
available_dates

# date control
select_start_date = Select(title = 'start date', 
					options = list(available_dates.keys()),
					value = list(available_dates.keys())[0])

select_end_date = Select(title = 'end date', 
					options = list(available_dates.keys()),
					value = list(available_dates.keys())[-1])

# strike control
strike_dict = {	'ALL' : 0, '1' : 1, '2' : 2,
				'4' : 4, '6' : 6, '8' : 8}

select_bracket = Select(title = 'bracket width', 
						options = list(strike_dict.keys()),
						value = list(strike_dict.keys())[0])

strike_dict[select_bracket.value]

# LOAD DATA
def get_df():
	start_date = int(available_dates[select_start_date.value])
	end_date = int(available_dates[select_end_date.value])
	df = opt.get_combined_df(start_date = start_date, end_date = end_date)
	return df

def load():
	global df
	df = get_df()
	if strike_dict[select_bracket.value] == 0:
		pass
	else:
		strikes = strike_dict[select_bracket.value]
		df = opt.strike_bracket(df, strikes)

load() # initial load


button_load = Button(label = 'load_data')
button_load.on_click(load)


# ---------------------------------------------------

# dte control
min_dte = Slider(title = 'DTE min limit', 
					start = 0, end = 1000, 
					value = 0)

max_dte = Slider(title = 'DTE max limit', 
					start = 0, end = 1000, 
					value = 1000)


# whats on the axis control
x_axis = Select(title="X Axis", options=list(df.columns), value="datetime")
y_axis = Select(title="Y Axis", options=list(df.columns), value="closePrice_qt")


def update_dte(attr, old, new):
	global selected
	selected = df[
			(df['daysToExpiration'] >= min_dte.value) &
			(df['daysToExpiration'] <= max_dte.value)
			]
	p.xaxis.axis_label = x_axis.value
	p.yaxis.axis_label = y_axis.value
	source.data = dict(
		x = selected[x_axis.value],
		y = selected[y_axis.value]
		)


for ctrl_dte in [min_dte, max_dte]:
	ctrl_dte.on_change('value', update_dte)


def update_axis(attr, old, new):
	selected = df.copy()
	p.xaxis.axis_label = x_axis.value
	p.yaxis.axis_label = y_axis.value
	source.data = dict(
		x = selected[x_axis.value],
		y = selected[y_axis.value]
		)

for ctrl_axis in [x_axis, y_axis]:
	ctrl_axis.on_change('value', update_axis)



# alpha slider
alpha_slider = Slider(title = 'Alpha', start = 0, end = 100, value = 50)

def change_alpha(attr, old, new):
	value = new
	source.data = dict(
		x = source.data['x'],
		y = source.data['y'],
		alpha = [value/100] * len(source.data['x']))

alpha_slider.on_change('value', change_alpha)




# PLOT 
p = figure(	height=600, width=700, 
			title="",
			tools="crosshair,pan,reset,save,wheel_zoom", 
			toolbar_location='right', 
			sizing_mode="scale_both")
p.scatter(x="x", y="y", size=4, alpha = "alpha", source=source, color="red")



# LAYOUT
controls = [select_start_date, 
			select_end_date,
			select_bracket, 
			button_load,
			min_dte,
			max_dte,
			x_axis, 
			y_axis]

inputs = column(controls, width = 200)
ctrl_plot = column(p, alpha_slider, sizing_mode="scale_both")

l = row(inputs, ctrl_plot)

curdoc().add_root(l)
curdoc().theme = 'dark_minimal'
curdoc().title = "plots"


