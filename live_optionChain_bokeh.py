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

import TDA_auth
import TDA_requests

TDA_auth.authenticate()

TDA_requests.import_credentials(auth_client_id = TDA_auth.client_id,\
								auth_access_token = TDA_auth.access_token)

# initial quotes bootstrap:

symbol = 'SPY'

def get_opts_from_API(symbol):
	query = TDA_requests.option_chain(symbol).copy()
	query.keys()
	opts_dict_list = []
	for contr_type in ['callExpDateMap', 'putExpDateMap']:
		contract = query[contr_type]
		expirations = contract.keys()
		for expiry in list(expirations):
			strikes = contract[expiry].keys()
			for st in list(strikes):
				entry = contract[expiry][st][0]
				opts_dict_list.append(entry)		
	idx = list(range(len(opts_dict_list)))
	opts_df = pd.DataFrame(opts_dict_list, index = idx)
	opts_df['underlying_mark'] = query['underlying']['mark']
	opts_df['log_diff'] = np.log(opts_df['strikePrice']/opts_df['underlying_mark'])
	print(opts_df)
	return opts_df


opts_df = get_opts_from_API(symbol)

# SOURCE
source = ColumnDataSource(data=dict(x=[], y=[], alpha = []))


def update(attr, old, new):
	p.xaxis.axis_label = x_axis.value
	p.yaxis.axis_label = y_axis.value
	selected = opts_df.copy()[
				(opts_df['daysToExpiration'] >= min_dte.value) &
				(opts_df['daysToExpiration'] <= max_dte.value)
				]
	source.data = dict(
		x=selected[x_axis.value],
		y=selected[y_axis.value],
		alpha=[alpha_slider.value/100] * len(selected[x_axis.value])
		)


# whats on the axis control

x_axis = Select(title="X Axis", options=list(opts_df.columns), value="strikePrice")
y_axis = Select(title="Y Axis", options=list(opts_df.columns), value="netChange")

for ax in [x_axis, y_axis]:
	ax.on_change('value', update)


# dte control
min_dte = Slider(title = 'DTE min limit', 
					start = 0, end = 1000, 
					value = 0)

max_dte = Slider(title = 'DTE max limit', 
					start = 0, end = 1000, 
					value = 1000)


for ctrl_dte in [min_dte, max_dte]:
	ctrl_dte.on_change('value', update)



# alpha slider
alpha_slider = Slider(title = 'Alpha', start = 0, end = 100, value = 50)

def change_alpha(attr, old, new):
	value = new
	source.data = dict(
		x = source.data['x'],
		y = source.data['y'],
		alpha = [value/100] * len(source.data['x']))

alpha_slider.on_change('value', change_alpha)


def load():
	opts_df = get_opts_from_API(symbol)
	p.xaxis.axis_label = x_axis.value
	p.yaxis.axis_label = y_axis.value
	selected = opts_df.copy()[
				(opts_df['daysToExpiration'] >= min_dte.value) &
				(opts_df['daysToExpiration'] <= max_dte.value)
				]
	source.data = dict(
		x=selected[x_axis.value],
		y=selected[y_axis.value],
		alpha=[alpha_slider.value/100] * len(selected[x_axis.value])
		)



# PLOT 
p = figure(	height=600, width=600, \
			title="PLOT",\
			tools="crosshair,pan,reset,save,wheel_zoom", \
			toolbar_location='right')

p.scatter(x="x", y="y", size=4, alpha = "alpha", source=source, color="red")


controls = column(\
					[x_axis,\
					 y_axis,\
					 min_dte,\
					 max_dte,\
					 alpha_slider],\
					 width = 200)

l = row(controls, p)

load()

# show(l)
curdoc().add_root(l)
curdoc().add_periodic_callback(load, 10000)
curdoc().theme = 'dark_minimal'
curdoc().title = "plots"


