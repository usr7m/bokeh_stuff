import datetime
import pandas as pd
import json
from pymongo import MongoClient

today = pd.to_datetime(datetime.datetime.today())
today	

''' initialize database engine '''
class mdb_cli():
	def __init__(self):
		pass
	def auth(self, user, pwd, host, port, auth_db):
		self.user = user
		self.pwd = pwd 
		self.host = host
		self.port = port
		self.auth_db = auth_db
		self.connection = 'mongodb://%s:%s@%s:%s/%s' \
						% (self.user, 
							self.pwd, 
							self.host, 
							self.port,
							self.auth_db)
	def connect(self, db):
		self.db = db
		self.connection = MongoClient(self.connection)
		self.client = self.connection[db]


mdb = mdb_cli()
mdb.auth(user = 'usr', 
      pwd = 'pwd',
      host = 'localhost', 
      port = '27017',
      auth_db = 'db')
mdb.connect(db = 'db')
mdb.client

start_date = int(pd.to_datetime('2021-04-01').timestamp() * 1000)
end_date = int(pd.to_datetime('2021-06-01').timestamp() * 1000)

class db_lookup():
	def __init__(self, symbol, start_date, end_date):
		self.symbol = symbol
		self.start_date = start_date
		self.end_date = end_date
	def look_up(self, collection):
		result = mdb.client[collection].aggregate(
			[
			    {
			        '$match': {
			            'datetime': {
			                '$gte': self.start_date,
			                '$lte': self.end_date
			            }
			        }
			    }
			]
		)
		return result
	def get_opts_df(self):
		query = list(
				self.look_up(
					collection = self.symbol + '_options'
					)
				)
		opts_dict_list = []
		for day in range(len(query)):
			on_date = dict(list(query)[day])
			for contr_type in ['callExpDateMap', 'putExpDateMap']:
				contract = on_date[contr_type]
				expirations = contract.keys()
				for expiry in list(expirations):
					strikes = contract[expiry].keys()
					for st in list(strikes):
						entry = contract[expiry][st][0]
						entry['datetime'] = on_date['datetime']
						opts_dict_list.append(entry)		
		idx = list(range(len(opts_dict_list)))
		self.opts_df = pd.DataFrame(opts_dict_list, index = idx)
	def get_quotes_df(self):
		query = list(
				self.look_up(
					collection = self.symbol + '_quotes'
					)
				)
		quotes_dict = []
		for i in range(len(query)):
			quote = dict(list(query)[i])
			entry = quote['quotes']
			entry['datetime'] = quote['datetime']
			quotes_dict.append(entry)
		idx = list(range(len(quotes_dict)))
		self.quotes_df = pd.DataFrame(quotes_dict, index = idx)
	def get_fundamentals_df(self):
		query = list(
				self.look_up(
					collection = self.symbol + '_fundamental'
					)
				)
		funds_dict = []
		for i in range(len(query)):
			fund = dict(list(query)[i])
			entry = fund['fundamental']
			entry['datetime'] = fund['datetime']
			funds_dict.append(entry)
		idx = list(range(len(funds_dict)))
		self.funds_df = pd.DataFrame(funds_dict, index = idx)
	def combine_df(self):
		combined_df = self.opts_df.merge(self.quotes_df, 
						on = 'datetime',
						suffixes = ['_opt', '_qt'])
		combined_df = combined_df.merge(self.funds_df, 
						on = 'datetime',
						suffixes = ['_qt', '_fnd'])
		self.combined_df = combined_df


def get_combined_df(symbol = 'SPY', start_date = start_date, end_date = end_date):
	d = db_lookup(symbol = symbol, start_date = start_date, end_date = end_date)
	d.get_opts_df()
	d.get_quotes_df()
	d.get_fundamentals_df()
	d.combine_df()
	return d.combined_df

def strike_bracket(opt_df, n):
	bracket_df = pd.DataFrame(columns = opt_df.columns)
	df = opt_df.copy()
	df = df[df['inTheMoney'] == False]
	for d in df['datetime'].unique():
		df_a = df.loc[df['datetime'] == d].copy()
		for dte in df_a['daysToExpiration'].unique():
			df_b = df_a.loc[df_a['daysToExpiration'] == dte].copy()
			for pC in df_b['putCall'].unique():
				if pC == 'CALL':
					df_c = df_b.loc[df_b['putCall'] == pC].copy()
					df_c.sort_values(by = 'strikePrice', ascending = True, inplace = True)
					df_c.reset_index(drop = True, inplace = True)
					bracket_df = bracket_df.append(df_c[:n])
				else:
					df_c = df_b.loc[df_b['putCall'] == pC].copy()
					df_c.sort_values(by = 'strikePrice', ascending = False, inplace = True)
					df_c.reset_index(drop = True, inplace = True)
					bracket_df = bracket_df.append(df_c[:n])
	return bracket_df
