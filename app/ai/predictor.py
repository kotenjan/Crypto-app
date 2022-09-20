from sklearn.preprocessing import PowerTransformer
from datetime import timedelta as td
import numpy as np
import time
from time import sleep
import pandas as pd
from utils.database import Database
from utils.logger import Logger
from ai.trainer import Trainer
from ai.extrema import Extrema
from random import randint


# This class is periodically predicting the next local exreme in real time
class Predictor:

    def __init__(self, timeout=60, short_timeout=30, window=50, columns=20):

        self.database = Database()
        self.trainer = Trainer()
        self.logger = Logger()
        self.timeout = timeout
        self.short_timeout = short_timeout
        self.extrema = Extrema()
        self.name = 'predictor'
        self.window = window
        self.columns = columns
        self.models = self.load_models()
        self.transformers = dict()
        self.chunk = 8196

    def reload_models(self):
        self.models = self.load_models()

    # Loads model weights into newly created models
    def load_models(self):

        model_time = self.trainer.get_model(window=self.window - 1, columns=self.columns)
        model_time.load_weights(f'/workspace/saved_model/model_time.hdf5')

        model_extreme = self.trainer.get_model(window=self.window - 1, columns=self.columns)
        model_extreme.load_weights(f'/workspace/saved_model/model_extreme.hdf5')
        
        return {'model_time': model_time, 'model_extreme': model_extreme}

    # Values are transformed before we use them as input for predictions
    def get_transformer(self, name, prediction):

        if name in self.transformers:
            if self.transformers[name]['usage'] < 120 + randint(-30, 30):
                self.transformers[name]['usage'] += 1
                return self.transformers[name]['prediction_transformer'] if prediction else self.transformers[name]['regular_transformer']

        regular_set, _ = self.extrema.get_prediction_set(name)
        prediction_set = regular_set[['interval_1', 'crypto_1']]
        
        regular_transformer = PowerTransformer()
        regular_transformer.fit(regular_set)

        prediction_transformer = PowerTransformer()
        prediction_transformer.fit(prediction_set)

        self.transformers[name] = {'regular_transformer': regular_transformer, 'prediction_transformer': prediction_transformer, 'usage': 0}
        return self.transformers[name]['prediction_transformer'] if prediction else self.transformers[name]['regular_transformer']

    def get_prediction(self, name, prediction_set):

        transformer = self.get_transformer(name, False)
        prediction_set = transformer.transform(prediction_set.tail(self.window - 1))
        prediction_set = np.array([prediction_set])

        prediction_time = self.models['model_time'].predict(prediction_set)
        prediction_extreme = self.models['model_extreme'].predict(prediction_set)

        return prediction_time, prediction_extreme

    # Transform the result of prediction back to real values
    def inverse_transform(self, time_data, extreme_data, transformer):
        df = pd.DataFrame()
        df['interval_1'] = time_data
        df['crypto_1'] = extreme_data
        prediction = transformer.inverse_transform(df)
        return prediction[0][0], prediction[0][1]

    # This is the format that is being shown to users in the gui table
    def create_prediction_dataframe(self, name, symbol, last_interval, time_data, extreme_data, prediction_time, prediction_extreme):
        row = [
            name, 
            symbol,
            last_interval[1], 
            last_interval[1] + td(minutes=int(time_data + last_interval[0])),
            last_interval[2],
            last_interval[2] + extreme_data,
            round(extreme_data/last_interval[2]*100, 3),
            prediction_time[0][0],
            prediction_extreme[0][0]
        ]
        return row

    def predict_value(self, names):

        predictions = pd.DataFrame(columns=['name', 'symbol', 'time_from', 'time_to', 'interval_from', 'interval_to','gain', 'transformed_time', 'transformed_gain'])

        for name in names:
            
            # User could've deleted the crypto and it takes up to one cycle to sync - that's why the try-except statement
            try:
                prediction_set, last_interval = self.extrema.get_prediction_set(name[0], self.chunk)
            except:
                continue

            if len(prediction_set) < 50:
                continue

            transformer = self.get_transformer(name[0], True)

            prediction_time, prediction_extreme = self.get_prediction(name[0], prediction_set)

            time_data, extreme_data = self.inverse_transform(prediction_time[0], prediction_extreme[0], transformer)
            
            predictions.loc[len(predictions)] = self.create_prediction_dataframe(name[0], name[1], last_interval, time_data, extreme_data, prediction_time, prediction_extreme)
        
        predictions =  predictions.set_index('name')
        
        return predictions

    # run from docker image as blocking call
    def loop(self):

        while True:
            try:
                time_start = time.perf_counter()

                names = self.database.get_names(symbols=True)
                
                predictions = self.predict_value(names)
                
                self.database.insert_into_prediction_table(predictions)

                self.logger.log(f"{self.name}")

                time_end = time.perf_counter()

                sleep(max(0, self.timeout - (time_end - time_start)))
            except Exception as e:
                self.logger.log(str(e))
                sleep(self.short_timeout)
