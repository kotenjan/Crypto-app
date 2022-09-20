from datetime import timedelta as td
from sklearn.preprocessing import PowerTransformer
import numpy as np
import pandas as pd
from itertools import islice
import json
import sys
from utils.database import Database
from utils.logger import Logger
from ai.extrema import Extrema
from ai.predictor import Predictor


# This class creates predictions for each minute in given dataset (based on previous local extremes)
# These predictions are then saved and used to find the best strategy/configuration for trading
class Interval:

    def __init__(self, timeout=120, short_timeout=60, window=50, lstm_columns=5, dense_columns=6):

        self.database = Database()
        self.logger = Logger()
        self.predictor = Predictor()
        self.timeout = timeout
        self.short_timeout = short_timeout
        self.extrema = Extrema()
        self.name = 'interval'
        self.window = window
        self.chunk = 8196
        self.lstm_columns = lstm_columns
        self.dense_columns = dense_columns

    # save all prediction sorted by time
    def save_as_json(self, data, name):
        with open(f'/workspace/data/{self.name}_{name.lower()}.json', 'w') as file:
            json.dump(data, file)

    # returns prediction of extreme and interval after which the extreme will occur
    def get_prediction(self, prediction_set, transformer):
        
        prediction_set = transformer.transform(prediction_set)
        
        prediction_set = np.array([prediction_set[-49:]])

        prediction_time = self.predictor.models['model_time'].predict(prediction_set)
        prediction_extreme = self.predictor.models['model_extreme'].predict(prediction_set)

        return prediction_time, prediction_extreme

    def take(self, n, iterable):
        return list(islice(iterable, n))

    # Returns data used for prediction
    def get_prediction_sets(self, df_trend, df_gold, df_vix, df_sap, df_crypto):
        
        end_date = df_trend.index[-1]
        start_date = df_trend.index[0]
        
        end_date = min(df_gold.index[-1], end_date)
        start_date = max(df_gold.index[0], start_date)

        end_date = min(df_vix.index[-1], end_date)
        start_date = max(df_vix.index[0], start_date)
        
        end_date = min(df_sap.index[-1], end_date)
        start_date = max(df_sap.index[0], start_date)

        end_date = min(df_crypto.index[-1], end_date)
        start_date = max(df_crypto.index[0], start_date)

        df_trend = df_trend[(df_trend.index <= end_date) & (df_trend.index >= start_date)]
        df_gold = df_gold[(df_gold.index <= end_date) & (df_gold.index >= start_date)]
        df_vix = df_vix[(df_vix.index <= end_date) & (df_vix.index >= start_date)]
        df_sap = df_sap[(df_sap.index <= end_date) & (df_sap.index >= start_date)]
        df_crypto = df_crypto[(df_crypto.index <= end_date) & (df_crypto.index >= start_date)]
        
        if len(df_crypto) == len(df_gold) == len(df_vix) == len(df_sap) == len(df_trend) > 200:
            return df_crypto, df_gold, df_vix, df_sap, df_trend
        else:
            self.logger.log('MISSING DATA')

    def get_transformer(self, data):
        transformer = PowerTransformer()
        transformer.fit(data)
        return transformer

    def get_result_transformer(self, prediction_set):
        prediction_set = prediction_set[['interval_1', 'crypto_1']]
        transformer = PowerTransformer()
        transformer.fit(prediction_set)
        return transformer

    # Create predictions for each minute
    def generate_intervals(self, name):

        variables = list()
        
        df_trend = self.database.select_all_from_and_fix_missing(name, 'trends', 'linear', replace_null=False, limit_area=None)
        df_gold = self.database.select_all_from_and_fix_missing('gold', 'gold', 'ffill', replace_null=True, limit_area=None)
        df_vix = self.database.select_all_from_and_fix_missing('vix', 'vix', 'ffill', replace_null=True, limit_area=None)
        df_sap = self.database.select_all_from_and_fix_missing('sap', 'sap', 'ffill', replace_null=True, limit_area=None)
        df_crypto = self.database.select_all_from_and_fix_missing(name, 'crypto', 'linear', replace_null=True, limit_area='inside').tail(200000)

        df_crypto, df_gold, df_vix, df_sap, df_trend = self.get_prediction_sets(df_trend, df_gold, df_vix, df_sap, df_crypto)
        full_data, _ = self.extrema.process_extremes(df_crypto, df_gold, df_vix, df_sap, df_trend)
        crypto_time = df_crypto.index

        transformer = self.get_transformer(full_data)
        result_transformer = self.get_result_transformer(full_data)
        
        for i in range(self.chunk, len(crypto_time)):

            data, last_interval = self.extrema.process_extremes(
                df_crypto.head(i).tail(self.chunk), 
                df_gold.head(i).tail(self.chunk), 
                df_vix.head(i).tail(self.chunk), 
                df_sap.head(i).tail(self.chunk), 
                df_trend.head(i).tail(self.chunk)
            )

            time_now = df_crypto.head(i).index[-1]

            if len(data) < 50:
                print(f'SKIPPING {len(data)}, {i}')
                continue

            prediction_time, prediction_extreme = self.get_prediction(data, transformer)

            # Prediction needs to be transformed back to its real value
            df = pd.DataFrame()
            df['interval_1'] = prediction_time[0]
            df['crypto_1'] = prediction_extreme[0]
            prediction = result_transformer.inverse_transform(df)
            end_time = last_interval[1] + td(minutes=int(prediction[0][0] + last_interval[0]))
            growth = prediction_extreme[0][0]
            interval = end_time - time_now

            variables.append([str(growth), str(interval.total_seconds()/60.0), str(df_crypto.head(i)['count'][-1]), str(i)])

            if i%100 == 0:
                print(time_now, i, name)
                self.save_as_json(variables, name)

    

if __name__ == '__main__':
    test = Interval()
    test.generate_intervals(sys.argv[1])
