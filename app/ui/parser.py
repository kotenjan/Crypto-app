from xml.etree.ElementInclude import include
from scipy.ndimage import gaussian_filter1d
import random
import numpy as np
from datetime import datetime as dt
from datetime import timedelta as td
from utils.database import Database
from utils.logger import Logger
import requests
import pytz

random.seed(10)

# process and fix data before sending them to frontend
class Parser:
    
    def __init__(self, cash=2000):
        date = dt.now()
        self.database = Database()
        self.logger = Logger()
        self.name = 'extreme'
        self.updates = {'date': '', 'flag': 0}
        self.colors = dict()
        self.config = np.array([  0.69,  -0.8 , -96.7 ,  57.43, 281.61,  15.63], dtype=float)
        self.cash = cash
        self.tz = pytz.timezone('UTC').localize(date) - pytz.timezone('Europe/Prague').localize(date).astimezone(pytz.timezone('UTC'))

    def get_data(self, names, limit):

        shared_data = {
            'vix': self.database.select_all_from_and_fix_missing('vix', 'vix', 'ffill', replace_null=True, limit_area=None, tail=2*limit),
            'sap': self.database.select_all_from_and_fix_missing('sap', 'sap', 'ffill', replace_null=True, limit_area=None, tail=2*limit),
            'gold': self.database.select_all_from_and_fix_missing('gold', 'gold', 'ffill', replace_null=True, limit_area=None, tail=2*limit),
        }

        named_data = {
            'trend': {},
            'crypto': {}
        }

        for name in names:
            named_data['trend'][name] = self.database.select_all_from_and_fix_missing(name, 'trends', 'linear', replace_null=False, limit_area=None, tail=2*limit)
            named_data['crypto'][name] = self.database.select_all_from_and_fix_missing(name, 'crypto', 'linear', replace_null=True, limit_area='inside', tail=2*limit)

        return shared_data, named_data

    def get_shared_dates(self, shared_data, named_data):
        
        end_date = dt.now()

        for x in shared_data:
            if shared_data[x] is not None:
                end_date = min(shared_data[x].index[-1], end_date)

        for x in named_data:
            for y in named_data[x]:
                if named_data[x][y] is not None:
                    end_date = min(named_data[x][y].index[-1], end_date)
        
        return end_date

    # datasets will all have last value at the same timestep (closest to datetime.now())
    def clip_data(self, shared_data, named_data, end_date):
        
        for x in shared_data:
            if shared_data[x] is not None:
                index = shared_data[x].index
                shared_data[x] = shared_data[x][(index <= end_date)]

        for x in named_data:
            for y in named_data[x]:
                if named_data[x][y] is not None:
                    index = named_data[x][y].index
                    named_data[x][y] = named_data[x][y][(index <= end_date)]

        return shared_data, named_data

    # google search data is too noisy so we use gaussian filter smoothing
    # the timestamp is also converted to keep only important info
    def process_data(self, shared_data, named_data, limit):
        
        label = [x.strftime('%m-%d %H:%M') for x in shared_data['gold'].tail(limit).index + self.tz]

        for x in shared_data:
            if shared_data[x] is not None:
                shared_data[x] = list(shared_data[x]['count'][-limit:])

        for x in named_data['crypto']:
            if named_data['crypto'][x] is not None:
                named_data['crypto'][x] = list(named_data['crypto'][x]['count'][-limit:])

        for x in named_data['trend']:
            if named_data['trend'][x] is not None:
                named_data['trend'][x] = list(gaussian_filter1d(named_data['trend'][x]['count'][-limit:], 15))

        return shared_data, named_data, label

    def get_linechart_data(self, names, limit):

        shared_data, named_data = self.get_data(names, limit)
            
        end_date = self.get_shared_dates(shared_data, named_data)

        self.updates = {'date': end_date, 'flag': int(not self.updates['flag'])}

        self.clip_data(shared_data, named_data, end_date)

        shared_data, named_data, label = self.process_data(shared_data, named_data, limit)

        return {'shared': shared_data, 'named': named_data, 'label': label}
    
    # chart line color
    def get_color(self):
        return "#"+''.join([random.choice('0123456789ABCDE') for _ in range(6)])

    # all overview chart datasets are aligned to the right
    def assign_label_to_data(self, data, label):

        to_fill = len(label) - len(data)

        label = label[-len(data):]        

        # if the dataset is too short it needs to have offset
        # offset is achieved by inserting empty dictionaries
        return [*[{} for _ in range(to_fill)], *[{'x': x, 'y': y} for x, y in zip(label, data)]]

    # prediction chart datasets are alligned to the left
    def assign_data_to_label(self, data, label):

        length = min(len(data), len(label))

        data = data[:length]
        label = label[:length]

        return [{'x': x, 'y': y} for x, y in zip(label, data)]

    # get data in format chart.js can render them in
    def create_dataset(self, data, config, axis, name, label, method):
        
        name = name + config['col_name']

        if name in self.colors:
            color = self.colors[name]
        else:
            color = self.get_color()
            self.colors[name] = color

        return {
            'label': name,
            'borderColor': color,
            'backgroundColor': color,
            'borderWidth': 2,
            'pointBorderColor': '#000000',
            'lineTension': 0,
            'pointRadius': 0,
            'pointBorderWidth': 0,
            'fill': False,
            'data': method(data, label),
            'yAxisID': axis,
            'hidden': True
        }

    # Get all data for overview chart 
    def build_dataset(self, limit):
        
        configs = {
            'crypto': {'col_name': ' Price in USD', 'y_axis': 'y1'},
            'trend': {'col_name': ' Google Trends', 'y_axis': 'y2'},
            'gold': {'col_name': 'Gold Price', 'y_axis': 'y3'},
            'vix': {'col_name': 'VIX', 'y_axis': 'y4'},
            'sap': {'col_name': 'S&P 500', 'y_axis': 'y5'},
        }

        axis_num = 1
        names = self.database.get_names()
        data = self.get_linechart_data(names, limit)
            
        if data is not None:

            datasets = list()

            for x in data['shared']:
                if data['shared'][x] is not None:
                    datasets.append(self.create_dataset(data['shared'][x], configs[x], f'y{axis_num}', '', data['label'], self.assign_label_to_data))
                    axis_num += 1
            for x in data['named']:
                for name in data['named'][x]:
                    if data['named'][x][name] is not None:
                        datasets.append(self.create_dataset(data['named'][x][name], configs[x], f'y{axis_num}', name, data['label'], self.assign_label_to_data))
                        axis_num += 1
            
            labels = data['label']
        else:
            datasets = []
            labels = []
            
        chart = {'update_flag': self.updates['flag'], 'labels': labels, 'datasets': datasets}

        return chart

    # simulate transactions to determine realtime gain
    def get_value(self, name):
        key = f'https://api.binance.com/api/v3/ticker/price?symbol={name}USDT'
        data = requests.get(key)  
        data = data.json()
        price = float(data['price'])
        return price
    
    # simulate transactions to determine realtime gain  
    def buy(self, name):

        purchases = self.database.select_all_from('purchases', 'purchases', 'name', 'name')
        value = self.get_value(name)
        cash = self.cash
        transactions = 0
        
        if purchases is not None:
            if name in purchases.index:

                cash = purchases['cash'][name]
                transactions = purchases['transactions'][name]

                if purchases['bought'][name]:
                    return

        self.database.insert_into_purchase_table([name, True, value, cash, transactions])
    
    # simulate transactions to determine realtime gain  
    def sell(self, name):

        purchases = self.database.select_all_from('purchases', 'purchases', 'name', 'name')
        value = self.get_value(name)

        if purchases is not None:
            if name in purchases.index:
                if purchases['bought'][name]:

                    transactions = purchases['transactions'][name] + 1
                    cash = float(purchases['cash'][name]) * (float(value) / float(purchases['value'][name]))
                    
                    self.database.insert_into_purchase_table([name, False, value, cash, transactions])
    
    # simulate transactions to determine realtime gain  
    def get_advice(self, growth, time_end, name):

        advice = 'wait'

        duration = time_end - dt.now()
        duration = duration.total_seconds()/60.0

        rising = self.config[0]
        sinking = self.config[1]
        time_buy_rising = self.config[2]
        time_sell_rising = self.config[3]
        time_buy_sinking = self.config[4]
        time_sell_sinking = self.config[5]

        if growth > rising:
            if duration > time_buy_rising:
                advice = 'buy'
            if duration <= time_sell_rising:
                advice = 'sell'
        if growth <= sinking:
            if duration < time_buy_sinking:
                advice = 'buy'
            if duration >= time_sell_sinking:
                advice = 'sell'

        if advice == 'buy':
            self.buy(name)
        if advice == 'sell':
            self.sell(name)

        return advice

    # Get data for gui prediction table
    def get_predicted_intervals(self):

        data = list()

        predictions = self.database.select_all_from('predictions', 'predictions', 'name', 'name')
        indexes = predictions.index
        names = self.database.get_names()
        
        for index, row in predictions.iterrows():
            if index in names:
                interval = dict()
                interval['name'] = index
                interval['symbol'] = row['symbol']
                interval['start_interval'] = (row['time_from'] + self.tz).strftime("%m-%d %H:%M")
                interval['end_interval'] = (row['time_to'] + self.tz).strftime("%m-%d %H:%M")
                interval['start_value'] = str(row['interval_from'])[:10]
                interval['end_value'] = str(row['interval_to'])[:10]
                interval['gain'] = str(row['gain']) + '%'
                interval['advice'] = self.get_advice(row['gain'], row['time_to'], index)
                data.append(interval)

        # there is a choice to return names=[BTC, ETH...] or names=[[BTC, 1234], [ETH, 5677]...] when symbols are true
        names = self.database.get_names(symbols=True)

        for name in names:
            if name[0] not in indexes:
                data.append({'name': name[0], 'symbol': name[1]})

        return data

    def add_name(self, name, symbol):
        names = self.database.get_names()
        if name in names:
            return f'Name {name} is already in database'

        self.database.insert_into_name_table(name, symbol)

    def remove_name(self, name):
        self.database.remove_from_name_table(name)

    def remove_table(self, name):
        self.database.remove_table(name, 'crypto')

    # create labels for prediction datasets
    def get_dataframe_sequence(self, min_date, max_date, include_last):
        
        if max_date <= min_date:
            return list()

        labels = list()

        while min_date < max_date:
            labels.append(min_date)
            min_date += td(minutes=1)

        if include_last:
            labels.append(max_date)

        return labels

    # return data for table that displays predictions
    def get_comparation_chart(self, limit):

        names = self.database.get_names()
        data = dict()

        for name in names:
            data[name] = self.database.select_all_from_and_fix_missing(name, 'crypto', 'linear', replace_null=True, limit_area='inside', tail=limit)

        predictions = self.database.select_all_from('predictions', 'predictions', 'name', 'name')
        intervals = dict()

        for index, row in predictions.iterrows():
            if index in names:
                interval = dict()
                interval['name'] = index
                interval['start_interval'] = row['time_from']
                interval['end_interval'] = row['time_to']
                interval['start_value'] = row['interval_from']
                interval['end_value'] = row['interval_to']
                intervals[index] = interval

        min_date = min([intervals[key]['start_interval'] for key in intervals])
        max_date = max([intervals[key]['end_interval'] for key in intervals])
        
        labels = self.get_dataframe_sequence(min_date, max_date, True)
        label_strings = [x.strftime('%m-%d %H:%M') for x in np.array(labels) + self.tz]

        datasets = list()
        axis_num = 1

        for key in intervals:

            start_labels = self.get_dataframe_sequence(min_date, intervals[key]['start_interval'], False)
            end_labels = self.get_dataframe_sequence(intervals[key]['start_interval'], intervals[key]['end_interval'], True)

            start_data = list(data[key][data[key].index.isin(start_labels)]['count'])
            end_data = list(np.linspace(start=float(intervals[key]['start_value']), stop=float(intervals[key]['end_value']), num=len(end_labels), endpoint=True))

            real_data = list(data[key][data[key].index.isin(labels)]['count'])
            predicted_data = [*start_data, *end_data]

            datasets.append(self.create_dataset(real_data, {'col_name': ' Real Values'}, f'y{axis_num}', key, label_strings, self.assign_data_to_label))
            datasets.append(self.create_dataset(predicted_data, {'col_name': ' Predicted Values'}, f'y{axis_num}', key, label_strings, self.assign_data_to_label))

            axis_num += 1

        self.updates = {'date': dt.now(), 'flag': int(not self.updates['flag'])}

        chart = {'update_flag': self.updates['flag'], 'labels': label_strings, 'datasets': datasets}

        return chart

            