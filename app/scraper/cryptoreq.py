from datetime import datetime as dt
from datetime import timedelta as td
import json
import pandas as pd
import requests
from time import sleep
import time
from utils.database import Database
from utils.logger import Logger


# Downloads cryptocurrency prices from coindesk.com
class CryptoReq:
    
    def __init__(self, timeout, short_timeout, scraping_window):
        self.url = 'https://www.coindesk.com/pf/api/v3/content/fetch/chart-api?query=%7B%22'
        self.url_website = '%22%7D&_website=coindesk'
        self.database = Database()
        self.name = 'crypto'
        self.timeout = timeout
        self.short_timeout = short_timeout
        self.scraping_window = scraping_window
        self.logger = Logger()

    def check_response(self, response):
        response_type = response.headers['Content-Type']
        response_code = response.status_code
        if response_code != 200:
            raise Exception(f'The request failed: API returned a response with code {response_code} of type {response_type}. {self.name}')

    def get_start_time(self, time):
        
        return dt.strftime(time, 'start_date%%22%%3A%%22%Y-%m-%dT%H%%3A%M')

    def get_end_time(self, time):
        
        return dt.strftime(time, 'end_date%%22%%3A%%22%Y-%m-%dT%H%%3A%M')

    def get_currency_name(self, name):
        
        return '%22%2C%22iso%22%3A%22' + name + '%22%2C%22ohlc%22%3Afalse%2C%22'

    def get_current_price(self, name):
        
        while True:
            try:
                current_time = dt.now()
                end_time = self.get_end_time(current_time)
                currency_name = self.get_currency_name(name)
                start_time = self.get_start_time(current_time - td(seconds=self.scraping_window))
                url = self.url + \
                      end_time + \
                      currency_name + \
                      start_time + \
                      self.url_website
                response = requests.get(url)
                self.check_response(response)
                data = json.loads(response.text)
                data = data['entries']
                return data
            except Exception as e:
                self.logger.log(str(e))
                sleep(self.short_timeout)
        
    # Download data for each cryptocurrency and save it in database
    def get_average_minute_value(self, names):

        end_date = dt.now()
        date = dt.strftime(end_date, '%Y-%m-%d %H:%M')
        date = dt.strptime(date, '%Y-%m-%d %H:%M')
        self.logger.log(f"{date} {self.name}")
        
        for name in names:
            data = self.get_current_price(name)
            data = pd.DataFrame.from_dict(data)
            data['date'] = pd.to_datetime(data[0], unit='ms', origin='unix').dt.floor('Min')
            data = data.set_index('date', drop=True)
            data[name] = data[1]
            data = pd.DataFrame(data[name])
            self.database.insert_into_history_table(self.name, data)

    def loop(self):
        
        while True:
            try:
                time_start = time.perf_counter()

                names = self.database.get_names()

                self.get_average_minute_value(names)
                time_end = time.perf_counter()
                sleep(max(0, self.timeout - (time_end - time_start)))
            except Exception as e:
                self.logger.log(str(e))
                sleep(self.short_timeout)
