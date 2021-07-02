from bokeh.models import Button, ColumnDataSource, Select, Slider, Label, TextInput
from bokeh.themes import built_in_themes
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.plotting import figure, show, output_file
import pandas as pd
import sys
import datetime
from math import pi

import query_mongo_template as qmt

def parse_datetime(df):
	df['datetime'] = pd.to_datetime(df['datetime'], unit = 'ms').dt.date


source_hist = ColumnDataSource(\
	data = dict(
		datetime = [],
		open = [], 
		high = [],
		low = [], 
		close = []
		)
	)


source_opts = ColumnDataSource(\
	data = dict(
		datetime = [],
		y = [],
		alpha = []
		)
	)



def data_parse(symbol):
		query = qmt.db_lookup(symbol.upper())
		query.get_hist_df()
		query.get_opts_df()
		hist = query.hist_df.copy()
		opts = query.opts_df.copy()	
		parse_datetime(hist)
		print(hist)
		parse_datetime(opts)
		print(opts)
		df = pd.merge(hist, opts, on = 'datetime', indicator = True)
		df = df[df['_merge'] == 'both']
		df.drop('_merge', axis = 1, inplace = True)
		df['datetime'] = pd.to_datetime(df['datetime'])
		df.reset_index(drop = True, inplace = True)
		return df


def get_expirations_list(df):
	expirations = pd.to_datetime(df['expirationDate'], unit = 'ms')
	expirations = list(expirations.dt.strftime('%Y-%m-%d').unique())
	return expirations


def load_data(symbol):
	global df
	try:
		df = data_parse(symbol = symbol)
		source_hist.data = dict(\
			datetime = df['datetime'],
			close = df['close']
			)
		source_opts.data = dict(\
			datetime = df['datetime'],
			y = df[y_axis_opts.value],
			alpha=[alpha_slider.value/100] * len(df['datetime'])
			)
		y_axis_opts.options = list(df.columns)
		date_selector_1.options = list(df['datetime'].dt.strftime('%Y-%m-%d').unique())
		x_axis_daily_1.options = list(df.columns)
		y_axis_daily_1.options = list(df.columns)
	except:
		print('there was an exception!..')
		pass



def update():
	symbol = ticker_text.value
	load_data(symbol)

def change_button_type():
	if button.button_type == 'success':
		button.button_type = 'warning'
	else:
		button.button_type = 'success'



'''		SET 1 		'''

width_1_1 = 150

ticker_text = TextInput(\
		title = 'ticker: ', value = 'SPY', width = width_1_1
		)


TOOLS = "pan,wheel_zoom,box_zoom,reset,save"
plot_1 = figure(\
		title = 'price',
			x_axis_type="datetime", tools = TOOLS, 
			plot_height = 300, plot_width = 800, 
			
			)
plot_1.scatter(\
			x = 'datetime', y = 'close', source = source_hist, 
			color = 'red', size = 5
			)


button = Button(\
		label = 'LOAD', button_type = 'success', width = width_1_1
		)

button.on_click(update)



set_1 = row(\
		plot_1,
		column(
			ticker_text, button
			)
		)




'''		SET 2 		'''

width_2_1 = 150

TOOLS_2 = "pan,wheel_zoom,box_zoom,reset,save"
plot_2 = figure(\
			title = 'option chain',
			x_axis_type="datetime", tools = TOOLS_2, 
			plot_height = 300, plot_width = 800, 	
			)
plot_2.scatter(\
			x = 'datetime', y = 'y', source = source_opts, 
			alpha = 'alpha', color = 'red', size = 5
			)

y_axis_opts = Select(\
			title="Y Axis", options = [], value="volatility", width = width_2_1
			)

def change_Y_axis(attr, old, new):
	source_opts.data['y'] = df[y_axis_opts.value]

y_axis_opts.on_change('value', change_Y_axis)


alpha_slider = Slider(\
			title = 'Alpha', start = 0, end = 100, value = 50, width = width_2_1
			)

def change_alpha(attr, old, new):
	source_opts.data['alpha'] = [new/100] * len(df['datetime'])

alpha_slider.on_change('value', change_alpha)





set_2 = row(\
		plot_2,
		column(\
			y_axis_opts,
			alpha_slider
			)
		)





'''		SET 3 		'''


source_daily_1 = ColumnDataSource(\
	data = dict(
		x_1 = [], y_1 = [], z_1 = [], alpha_1 = []
		)
	)

label = Label(\
		x = 10, y = 10,
		text=str(''), text_font_size='24px', text_color='#eeeeee'
		)

plot_3_1 = figure(\
		title = '3_1', plot_height = 600, plot_width = 800, 	
		)
plot_3_1.scatter(\
		x = 'x_1', y = 'y_1', source = source_daily_1, 
		alpha = 'alpha_1', color = 'red', size = 5
		)
plot_3_1.add_layout(label)




										# date control

width_3_1 = 150

date_selector_1 = Select(\
			title = 'title', options = [], value = '', width = width_3_1
			)

										# axis controls

x_axis_daily_1 = Select(\
			title="X Axis", options = [], value="strikePrice", width = width_3_1 
			)
y_axis_daily_1 = Select(\
			title="Y Axis", options = [], value="netChange", width = width_3_1
			)

										# dte controls

min_dte_1 = Slider(\
			title = 'DTE min limit', 
			start = 0, end = 1000, value = 0, width = width_3_1
			)
max_dte_1 = Slider(\
			title = 'DTE max limit', 
			start = 1, end = 1000, value = 1000, width = width_3_1
			)
								
										# LOG_DIFF control

ctrl_log_diff_1 = Slider(\
	title = 'log_diff limit', 
	start = 0.001, end = 1, step = 0.001, value = 1, width = width_3_1)


										# alpha slider
alpha_slider_1 = Slider(\
	title = 'Alpha', start = 0, end = 100, value = 50, width = width_3_1
	)

def change_alpha_1(attr, old, new):
	value = new
	source_daily_1.data = dict(\
		x_1 = source_daily_1.data['x_1'],
		y_1 = source_daily_1.data['y_1'],
		z_1 = source_daily_1.data['z_1'],
		alpha_1 = [value/100] * len(source_daily_1.data['x_1'])
		)

alpha_slider_1.on_change('value', change_alpha_1)



def update_daily(attr, old, new):
	min_dte_1.end = max_dte_1.value
	max_dte_1.start = min_dte_1.value
	df_s = df.loc[df['datetime'] == pd.to_datetime(date_selector_1.value)].copy()
	df_s.reset_index(drop = True, inplace = True)
	''''''
	plot_3_1.xaxis.axis_label = x_axis_daily_1.value
	plot_3_1.yaxis.axis_label = y_axis_daily_1.value
	df_s = df_s[\
		(df_s['daysToExpiration'] >= min_dte_1.value) &
		(df_s['daysToExpiration'] <= max_dte_1.value) &
		(abs(df_s['log_diff']) <= ctrl_log_diff_1.value)
		]
	df_s.reset_index(drop = True, inplace = True)
	source_daily_1.data = dict(
		x_1 = df_s[x_axis_daily_1.value],
		y_1 = df_s[y_axis_daily_1.value],
		z_1 = df_s['underlyingMark'],
		alpha_1 = [alpha_slider.value/100] * len(df_s[x_axis_daily_1.value]))
	label.x = df_s[x_axis_daily_1.value].min() + 10
	label.y = df_s[y_axis_daily_1.value].min() + 10
	label.text = str(df_s['underlyingMark'][0])



for control in [date_selector_1, x_axis_daily_1, y_axis_daily_1,
				min_dte_1, max_dte_1, ctrl_log_diff_1]:
	control.on_change('value', update_daily)



set_3 = row(\
		plot_3_1,
		column(
			date_selector_1,
			x_axis_daily_1,
			y_axis_daily_1,
			min_dte_1,
			max_dte_1,
			ctrl_log_diff_1,
			alpha_slider_1
			)
		)


layout = column(set_1, set_2, set_3)


curdoc().add_root(layout)
curdoc().theme = 'dark_minimal'
curdoc().title = "plots"




