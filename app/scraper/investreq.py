from datetime import datetime as dt
from datetime import timedelta as td
import json
import pandas as pd
from time import sleep
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from utils.database import Database
from utils.logger import Logger


# Downloading the value/price of cryptocurrencies, gold, vix and s&p 500
class InvestReq:
    
    def __init__(self, timeout, short_timeout, scrape_days=7):
        
        self.database = Database()
        self.timeout = timeout
        self.short_timeout = short_timeout
        self.page_load_timeout = 1000
        self.logger = Logger()
        self.scrape_days = scrape_days

    # the scraping of the data requires selenium
    # these parameters are used for the driver
    def get_driver(self):

        options = Options()    
        options.add_argument('--no-sandbox')
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--profile-directory=Default')

        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(self.page_load_timeout)
        return driver

    # downloading data when the previous download was less than 120 minutes ago (there is a different approach for long-term downloads)
    def get_current_price(self, symbol):
        while True:
            try:
                driver = self.get_driver()
                path = f'https://api.investing.com/api/financialdata/{symbol}/historical/chart/?interval=PT1M&pointscount=120'
                driver.get(path)
                response = driver.find_element(By.TAG_NAME, 'body')
                data = json.loads(response.text)
                driver.quit()
                data = data['data']
                return data
            except Exception as e:
                self.logger.log(str(e))
                sleep(self.short_timeout)
    
    def get_path(self, start_time, end_time, symbol):
        start_timestamp = 'from=' + str(int(start_time.timestamp()))
        end_timestamp = 'to=' + str(int(end_time.timestamp()))
        url = f'https://tvc4.investing.com/9e1424a21a8aaa6005b92a527fdff8de/0/1/1/8/history?symbol={symbol}&resolution=1&'

        path = url + \
                start_timestamp + \
                '&' + \
                end_timestamp
        return path

    # Download data further in the past
    def get_historical_interest_window(self, start_time, end_time, symbol):
        while True:
            try:
                driver = self.get_driver()
                path = self.get_path(start_time, end_time, symbol)
                driver.get(path)
                response = driver.find_element(By.TAG_NAME, 'body').text
                driver.quit()
                data = json.loads(response)
                return data
            except Exception as e:
                self.logger.log(str(e))
                sleep(self.short_timeout)

    def get_startdate_timestamp(self, name, type_name):
        
        start_time = dt.now() - td(days=self.scrape_days)

        last_time = self.database.select_last_date(name, type_name)
        
        if last_time:
            start_time = last_time
        else:
            self.logger.log(f'USING START DATE {start_time}')

        return start_time

    def get_enddate_timestamp(self):
        
        return dt.now()
        
    # The data is being periodically downloaded
    def get_average_minute_value(self, symbol, name, type_name):

        start_date = self.get_startdate_timestamp(name, type_name) 
        end_date = self.get_enddate_timestamp()
        timeframe = end_date - start_date

        # How far in the past was the last download - which download method to use
        # both use selenium but download from different source
        if timeframe.total_seconds() >= 7200:
            
            range_get = td(days=5)
            range_add = td(days=3)
            
            while start_date <= end_date - td(seconds=7200):

                current_end_date = min(start_date + range_get, end_date)
                data = self.get_historical_interest_window(start_date, current_end_date, symbol)
                if data['s'] == 'no_data':
                    raise ValueError(f'NO DATA RECEIVED FOR [{name}, {symbol}, {type_name}]')
                data = pd.DataFrame.from_dict(data)
                data['date'] = pd.to_datetime(data['t'], unit='s', origin='unix').dt.floor('Min')
                data = data.set_index('date', drop=True)
                data[name] = data[['c', 'o', 'h', 'l']].mean(axis=1)
                data = pd.DataFrame(data[name])
                self.database.insert_into_history_table(type_name, data)
                
                self.logger.log(f"{start_date} --> {current_end_date} {name}")
                start_date += range_add
                sleep(self.short_timeout)
        else:

            data = self.get_current_price(symbol)
            data = pd.DataFrame.from_dict(data)
            data['date'] = pd.to_datetime(data[0], unit='ms', origin='unix').dt.floor('Min')
            data = data.set_index('date', drop=True)
            data[name] = data[[1, 2, 3, 4]].mean(axis=1)
            data = pd.DataFrame(data[name])
            self.database.insert_into_history_table(type_name, data)
            self.logger.log(f"{start_date} --> {end_date} {name}")

    def loop(self):

        market_symbols = [
            [8830, 'gold', 'gold'],
            [44336, 'vix', 'vix'],
            [166, 'sap', 'sap'],
        ]

        # separately downloading cryptocurrencies and gold/vix/sap
        while True:
            try:
                time_start = time.perf_counter()

                crypto_symbols = self.database.get_names(symbols=True)
                
                for name, symbol in crypto_symbols:
                    try:
                        self.get_average_minute_value(symbol, name, 'crypto')
                        sleep(self.short_timeout)
                    except Exception as e:
                        self.logger.log(f'CANNOT DOWNLOAD [{name}, {symbol}, crypto]')
                        self.logger.log(str(e))
                        sleep(self.short_timeout)
                
                for symbol in market_symbols:
                    try:
                        self.get_average_minute_value(*symbol)
                        sleep(self.short_timeout)
                    except Exception as e:
                        self.logger.log(f'CANNOT DOWNLOAD {symbol}')
                        self.logger.log(str(e))
                        sleep(self.short_timeout)

                time_end = time.perf_counter()
                sleep(max(0, self.timeout - (time_end - time_start)))
            except Exception as e:
                self.logger.log(str(e))
                sleep(self.short_timeout)
