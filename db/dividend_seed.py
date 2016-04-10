#import pandas as pd
import time
import multiprocessing
import subprocess
import psycopg2
import getpass
import sys
import csv
import Quandl
"""
This file seeds the database with data from dividend data from the Quandl API

UPDATED: 2013-04-04 2016-04-04
"""

#Stocks files
stock_files   = ["nasdaq.csv", "amex.csv", "nyse.csv"]

def get_ticker_list(cursor, conn):
	"""Open the available lists of stocks, extract their tickers, and call create_stocks

	Params: cursor (database cursor)
	Returns: ticker_list (list of stock tickers)
	"""
	ticker_list = []
	for stock_file in stock_files:
		with open(stock_file, 'r') as csvfile:
			firstline = True
			reader = [row for row in csv.reader(csvfile.read().splitlines())]
			for row in reader:
				if firstline:
					firstline = False
					continue
				ticker_list.append(row[0])
	return(ticker_list)
	


 
def get_dividend_history(ticker_list, cur, conn, argv):
	"""
	Use Quandl API to get stock data for past 40 years and pass data to create_stock_price
        Params: ticker_list, names_list (stock names), index (stock index), cursor (database cursor)
	"""
	for ticker in ticker_list:
		#Deal w/ data-cleaning issue
		if ticker == "MSG":
			continue
		date1 = argv[1]
		date2 = argv[2]
		print(ticker)
		#history = Quandl.get(ticker, trim_start=date1, trim_end=date2, authoken ="8mshdZsFsubUH3YuALqR", returns =" numpy")
		history = Quandl.get(ticker, authoken ="8mshdZsFsubUH3YuALqR")
		print(history)


def create_dividend(ticker, history, cur, conn):
	"""
	Enter stock prices into Stock_price relation
	params: ticker, history (list of hashes, each hash contains data on a given date for the given stock), cur, 
	"""
	#print("Creating stock price entry for: {}".format(ticker))
	for date in history:
		try:
			day = date['Date']
		except KeyError as e:
			print(str(e))
			continue
		try:
			open_price = date['Open']
		except KeyError:
			print(str(e))
			continue
		try:
			close_price = date['Close']
		except KeyError:
			print(str(e))
			continue
		data = (ticker, day, float(open_price), float(close_price))
		#print(str(data))
		SQL = "INSERT INTO stock_dividend(ticker, pdate, open_price, close_price) VALUES (%s, %s, %s, %s);"
		execute(cur, conn, data, SQL)	
	conn.commit()

def execute(cur, conn, data, SQL):
	try:
		cur.execute(SQL, data)
	#except psycopg2.IntegrityError as e:
	#	print(str(e))
	#	print(str(data))
	#	sys.exit(0)
	#except psycopg2.DataError as e:
	#	print(str(e))
	#	print(data)
	#except psycopg2.InternalError as e:
	#	print(str(e))
	#	sys.exit(0)
	#except psycopg2.ProgrammingError as e:
	#	print(str(e))
	#	sys.exit(0)
	#except KeyError as e:
	#	print(str(e))
	except Exception as e:
		print(str(e))	

def process_launch_stocks(processes, ticker_list, cur, conn, argv):
	"""
	Pass the ticker list in chunks to the API for processing.
	Leverage multiprocessing.
	"""
	chunk_size = int(len(ticker_list) / processes)
	processes = []
	for i in range(0, len(ticker_list), chunk_size):
		chunk = ticker_list[i: i + chunk_size]
		p = multiprocessing.Process(target=get_history, args=(chunk, cur, conn,argv,))
		processes.append(p)
		p.start()
	for process in processes:
		process.join()


def main(argv):
	try:
		conn = psycopg2.connect(database = "caweinsh_sp3", user = "caweinsh", password = getpass.getpass())
	except StandardError as e:
		print(str(e))
		exit
	cur = conn.cursor()
	ticker_list = get_ticker_list(cur, conn)
	#Launch multithreading to handle  API data
	#process_launch_stocks(24, ticker_list, cur, conn, argv)
	get_dividend_history(ticker_list, cur, conn, argv)
	cur.close()	
	conn.close()
	print("Complete: " + str(argv[1]) + " " +  str(argv[2]))

main(sys.argv)
