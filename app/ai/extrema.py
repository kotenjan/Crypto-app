import numpy as np
import pandas as pd
from scipy.signal import argrelextrema
from scipy.ndimage import gaussian_filter1d
from utils.database import Database
from utils.logger import Logger
from ai.minmax import Minmax


# This class creates dataset in a format that can be used as an input to the predicting model
class Extrema:
    
    # The parameters are:
    # value of sigma in the gaussian filter for smoothing of the cryptocurrency price values
    # list with the size of sigmas in gaussian filter for creating other columns based on the original dataset
    def __init__(self, window=15, intervals=[15, 60, 240]):
        self.window = window
        self.intervals = intervals
        self.database = Database()
        self.logger = Logger()
        self.minmax = Minmax()
        self.name = 'extreme'

    def get_average_diff(self, arr):
        return np.abs(arr[:-1] - arr[1:]).mean()

    # Method, which will pick data from given dataset specifically from positions of found local extremes
    def describe(self, extremes, df, name, include_realtime_data=False):

        idx = df.index[extremes]
        last_val = 0
        arr = np.array(df['count'], dtype='float')
        # creates column for each value of sigma from specified dataset
        arrs = [gaussian_filter1d(arr, interval)[extremes] for interval in self.intervals]
        
        dcts = dict()
        # includes the time of local extremes in dataset
        if include_realtime_data:
            dcts['interval_1'] = extremes
            dcts[f'{name}_1'] = arr[extremes]
            dcts = {**dcts, **{f'{name}_{i}': arr for arr, i in zip(arrs, self.intervals)}}

            last_val = dcts[f'{name}_1'][-1] if len(dcts) else 0

        else:
            dcts = {f'{name}_{i}': arr for arr, i in zip(arrs, self.intervals)}
        dcts['date'] = idx
        
        df = pd.DataFrame.from_dict(dcts)
        df = df.set_index('date')
        df = df.diff()
        df = df[1:]       

        return df, last_val

    # specified times of local extremes have different structure than other types of data
    # it has a constantly upgoing trend 
    # it is necessary to subtract twice it's neighbors to make that data stationary
    # this method does exactly that
    # it creates more columns with gaussian filter smoothing
    def describe_time(self, df):
        idx = df.index
        arr = np.array(df['interval_1'], dtype='float')

        last_val = arr[-1] if len(arr) else 0
        last_id = idx[-1] if len(arr) else 0
        
        arrs = [gaussian_filter1d(arr, interval) for interval in self.intervals]
        dcts = {f'interval_{i}': arr for arr, i in zip(arrs, self.intervals)}
        dcts['date'] = idx

        time_extremes = pd.DataFrame.from_dict(dcts)
        time_extremes = time_extremes.set_index('date')
        time_extremes = time_extremes.diff()

        return time_extremes, last_val, last_id
            
    # Zde se volají jednotlivé metody na vytvoření datasetu na základě lokálních extrémů kryptoměn 
    # This method is creating distinct datasets with values being picked based on local extremes in cryptocurrency values
    # created datasets are joined into one
    def process_extremes(self, crypto, gold, vix, sap, trend):

        # creating local extremes
        extremes, _ = self.minmax.find_extremes(np.array(crypto['count'], dtype='float'), False)

        # selecting data from other datasets based on local extremes
        crypto_extremes, crypto_last_interval = self.describe(extremes, crypto, 'crypto', True)
        gold_extremes, _ = self.describe(extremes, gold, 'gold', False)
        vix_extremes, _ = self.describe(extremes, vix, 'vix', False)
        sap_extremes, _ = self.describe(extremes, sap, 'sap', False)
        trend_extremes, _ = self.describe(extremes, trend, 'trend', False)
        time_extremes, time_last_interval, last_date = self.describe_time(crypto_extremes)
        
        result = pd.concat(
            [
                crypto_extremes,
                gold_extremes,
                vix_extremes,
                sap_extremes,
                trend_extremes,
                time_extremes
            ], 
            axis=1, 
            join='inner'
        )
        
        last_interval = (time_last_interval, last_date, crypto_last_interval) if len(result) else (0, 0, 0)
        result['interval_1'] = result['interval_1'].diff()
        result = result[1:]        

        return result, last_interval

    def get_prediction_set(self, name, tail=None):

        # collecting all datasets from database
        df_trend = self.database.select_all_from_and_fix_missing(name, 'trends', 'linear', replace_null=False, limit_area=None, tail=tail)
        end_date = df_trend.index[-1]
        start_date = df_trend.index[0]

        df_gold = self.database.select_all_from_and_fix_missing('gold', 'gold', 'ffill', replace_null=True, limit_area=None, tail=tail)
        end_date = min(df_gold.index[-1], end_date)
        start_date = max(df_gold.index[0], start_date)

        df_vix = self.database.select_all_from_and_fix_missing('vix', 'vix', 'ffill', replace_null=True, limit_area=None, tail=tail)
        end_date = min(df_vix.index[-1], end_date)
        start_date = max(df_vix.index[0], start_date)

        df_sap = self.database.select_all_from_and_fix_missing('sap', 'sap', 'ffill', replace_null=True, limit_area=None, tail=tail)
        end_date = min(df_sap.index[-1], end_date)
        start_date = max(df_sap.index[0], start_date)

        df_crypto = self.database.select_all_from_and_fix_missing(name, 'crypto', 'linear', replace_null=True, limit_area='inside', tail=tail)
        end_date = min(df_crypto.index[-1], end_date)
        start_date = max(df_crypto.index[0], start_date)
        
        # selecting common interval of all the datasets closest to the last inserted date
        df_trend = df_trend[(df_trend.index <= end_date) & (df_trend.index >= start_date)]
        df_gold = df_gold[(df_gold.index <= end_date) & (df_gold.index >= start_date)]
        df_vix = df_vix[(df_vix.index <= end_date) & (df_vix.index >= start_date)]
        df_sap = df_sap[(df_sap.index <= end_date) & (df_sap.index >= start_date)]
        df_crypto = df_crypto[(df_crypto.index <= end_date) & (df_crypto.index >= start_date)]

        if len(df_crypto) == len(df_gold) == len(df_vix) == len(df_sap) == len(df_trend):
            extremes, last_interval = self.process_extremes(df_crypto, df_gold, df_vix, df_sap, df_trend)
            return extremes, last_interval
        else:
            self.logger.log('MISSING DATA')
            return


if __name__ == '__main__':
    extrema = Extrema()
    names = Database.get_names()
    for name in names:
        print(extrema.get_prediction_set(name))
    