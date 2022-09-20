from datetime import datetime as dt
from datetime import timedelta as td
import json
import pandas as pd
import requests
from time import sleep
import time
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from utils.database import Database
from utils.logger import Logger


# Downloads data about searches on Google Search
class TrendReq(object):
    
    def __init__(self, timeout, short_timeout, trend_timeout, scrape_days=7):
        
        self.general_url = 'https://trends.google.com/trends/api/explore'
        self.interest_over_time_url = 'https://trends.google.com/trends/api/widgetdata/multiline'
        self.tz = 0
        self.hl = 'en-US'
        self.geo = ''
        self.cat = 7
        self.request_timeout = (5, 10)
        self.cookies = self.GetGoogleCookie()
        self.database = Database()
        self.timeout = timeout
        self.trend_timeout = trend_timeout
        self.short_timeout = short_timeout
        self.name = 'trends'
        self.logger = Logger()
        self.scrape_days = scrape_days

    # Get configuration before downloading the actual data
    def GetGoogleCookie(self):
        
        return dict(filter(lambda i: i[0] == 'NID', requests.get(
            'https://trends.google.com/?geo={geo}'.format(
                geo=self.hl[-2:]),
            timeout=self.request_timeout,
            proxies=''
        ).cookies.items()))

    def check_response(self, response):
        response_type = response.headers['Content-Type']
        response_code = response.status_code
        if response_code != 200:
            raise Exception(f'The request failed: Google returned a response with code {response_code}.')
        if 'application/json' not in response_type:
            if 'application/javascript' not in response_type:
                if 'text/javascript' not in response_type:
                    raise Exception(f'The request failed: Google returned a response with content {response_type}.')

    # Download data
    def get_data(self, url, trim_chars=0, **kwargs):
        
        s = requests.session()

        retry = Retry(connect=2, backoff_factor=10)
        adapter = HTTPAdapter(max_retries=retry)
        s.mount('http://', adapter)
        s.mount('https://', adapter)
        
        s.headers.update({'accept-language': self.hl})
        
        response = s.get(
            url, 
            timeout=self.request_timeout, 
            cookies=self.cookies, 
            **kwargs
        )  

        self.check_response(response)
        content = response.text[trim_chars:]
        return json.loads(content)

    # Prepare parameters for request.get call
    def get_payload(self, keyword, timeframe):
        
        payload = {
            'cat': self.cat,
            'hl': self.hl,
            'tz': self.tz,
            'req': {'comparisonItem': [
                {
                    'keyword': keyword,
                    'time': timeframe,
                    'geo': self.geo
                }
            ]},
        }

        payload['req'] = json.dumps(payload['req'])
        return payload

    # Makes request to Google, gets interest over time
    def get_widget(self, payload):
        
        widget_dicts = self.get_data(
            url=self.general_url,
            params=payload,
            trim_chars=4,
        )['widgets']

        for widget in widget_dicts:
            if widget['id'] == 'TIMESERIES':
                return widget

    # Get data
    def interest_over_time(self, widget, keyword):
        
        over_time_payload = {
            # convert to string as requests will mangle
            'req': json.dumps(widget['request']),
            'token': widget['token'],
            'tz': self.tz
        }

        # get data and parse them
        req_json = self.get_data(
            url=self.interest_over_time_url,
            trim_chars=5,
            params=over_time_payload,
        )

        df = pd.DataFrame(req_json['default']['timelineData'])
        df['date'] = pd.to_datetime(df['time'].astype(dtype='float64'), unit='s')
        df = df.set_index(['date']).sort_index()

        return pd.DataFrame(df['value'].to_list(), columns=[keyword], index=df.index)

    # Gets minute data for interest up to H:4, M:29 which is dataframe of length 270
    def get_historical_interest_window(self, keyword, start_date, end_date):

        # formating date to comply with API call
        start_date_str = start_date.strftime('%Y-%m-%dT%H\\:%M\\:00')
        end_date_str   =   end_date.strftime('%Y-%m-%dT%H\\:%M\\:00')

        tf = start_date_str + ' ' + end_date_str

        while True:
            payload = self.get_payload(keyword, tf)
            widget = self.get_widget(payload)
            df = self.interest_over_time(widget, keyword)
            return df
    
    def get_from_timestamp(self, name):
        
        start_time = dt.now() - td(days=self.scrape_days)

        last_time = self.database.select_last_date(name, self.name)
        
        if last_time:
            start_time = last_time
        else:
            self.logger.log(f'USING START DATE {start_time}')
        
        return start_time

    def get_to_timestamp(self):
        
        return dt.now()

    def get_historical_interest(self, keyword):

        start_date = self.get_from_timestamp(keyword)
        end_date = self.get_to_timestamp()
        
        end_date = min(end_date, dt.now())
        range_get = td(hours=4, minutes=29)
        range_add = td(hours=4, minutes=30)
        while start_date < end_date:
            current_end_date = min(start_date + range_get, end_date)
            data = self.get_historical_interest_window(keyword, start_date, current_end_date)
            self.database.insert_into_history_table(self.name, data)
            self.logger.log(f"{start_date} --> {end_date} {self.name} {keyword}")
            start_date += range_add
            sleep(self.trend_timeout)
        sleep(self.short_timeout)

    def loop(self):
        
        while True:
            try:
                time_start = time.perf_counter()

                names = self.database.get_names()

                for name in names:
                    self.get_historical_interest(name)

                time_end = time.perf_counter()
                sleep(max(0, self.timeout - (time_end - time_start)))
            except Exception as e:
                self.logger.log(str(e))
                sleep(self.short_timeout)
    