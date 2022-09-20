import numpy as np
from sklearn.preprocessing import PowerTransformer
from keras.layers import Dense, LSTM
from keras.models import Sequential
from keras.callbacks import ModelCheckpoint, EarlyStopping
import time
from time import sleep
from tensorflow.keras.optimizers import Adam
from utils.database import Database
from utils.logger import Logger
from ai.extrema import Extrema


# Creating and training of prediction model
class Trainer:

    def __init__(self, timeout=3600):
        self.database = Database()
        self.extrema = Extrema()
        self.logger = Logger()
        self.timeout = timeout
        self.name = 'trainer'

    # The dataset is split into sorted chunks (50 data rows per chunk by default) for prediction blocks with memory (LSTM)
    # split into train/test (validation set is derived from train later)
    def create_train_set(self, names, window, test_size):
        
        X_train = list()
        Y_train = list()
        X_test = list()
        Y_test = list()

        for name in names:
            df, _ = self.extrema.get_prediction_set(name)
            df.to_csv(f'/workspace/data/extreme_{name.lower()}.csv')
            df = PowerTransformer().fit_transform(df)

            length = len(df)
            test_len = int(length*test_size)
            train_len = length - test_len

            for i in range(len(df) + 1 - window - test_len):
                chunk = df[i:i+window]
                x = chunk[:-1]
                y = chunk[-1]
                X_train.append(x)
                Y_train.append([y[0], y[1]])

            for i in range(train_len, len(df) + 1 - window):
                chunk = df[i:i+window]
                x = chunk[:-1]
                y = chunk[-1]
                X_test.append(x)
                Y_test.append([y[0], y[1]])

        return np.array(X_train), np.array(X_test), np.array(Y_train), np.array(Y_test)

    # Prediction model architecture
    def get_model(self, window, columns):
        
        model = Sequential()

        # LSTM

        model.add(
            LSTM(
                units=20, 
                input_shape=(window, columns), 
                return_sequences=True,
                dropout=0.2,
            )
        )
        
        # LSTM

        model.add(
            LSTM(
                units=4, 
                input_shape=(None, None), 
                return_sequences=False,
                dropout=0.2,
            )
        )

        # DENSE

        model.add(
            Dense(
                1
            )
        )

        model.compile(loss='mae', optimizer=Adam(learning_rate=0.001))

        return model
    
    def train_test_split(self, X, Y, test_size):
        length = len(X)
        test_len = int(length*test_size)
        train_len = length - test_len        
        X_train, X_test, Y_train, Y_test = X[:train_len], X[-test_len:], Y[:train_len], Y[-test_len:]
        return X_train, X_test, Y_train, Y_test

    # Split to train/validation/test, Train model, save on new lowest validation error, print MAE of result
    # If epochs are 0, model is not being trained, only shows MAE result
    def evaluate_model(self, X_train, X_test, Y_train, Y_test, window, columns, name, epochs, load_weights):
        
        X_train, X_val, Y_train, Y_val = self.train_test_split(X_train, Y_train, test_size=0.5)
        model = self.get_model(window, columns)
        if load_weights:
            model.load_weights(f'{name}.hdf5')
        if epochs > 0:
            save_callback = ModelCheckpoint(f'{name}.hdf5', monitor='val_loss', verbose=1, save_weights_only=True, save_best_only=True, mode='auto', save_freq='epoch')
            stop_callback = EarlyStopping(monitor='val_loss', patience=200)
            model.fit(X_train, Y_train, validation_data=(X_val, Y_val), batch_size=64, epochs=epochs, callbacks=[save_callback, stop_callback])
        model.evaluate(X_test, Y_test, batch_size=64, verbose=2)

        print(f'MEAN ABSOLUTE ERROR: {np.mean(np.abs(model.predict(X_test) - Y_test))}')
    
    def make_predictor(self, X_train, X_test, Y_train, Y_test, filename, epochs, load_weights):
        self.evaluate_model(X_train, X_test, Y_train, Y_test, X_train.shape[1], X_train.shape[2], f'/workspace/saved_model/{filename}', epochs, load_weights)

    def create_models(self, names, window, cycles_t, load_model_t, cycles_e, load_model_e):
        
        X_crypto_train, X_crypto_test, Y_train, Y_test = self.create_train_set(names, window, 0.5)
        
        Y_time_train = np.array([y[0] for y in Y_train])[:, np.newaxis]
        Y_extreme_train = np.array([y[1] for y in Y_train])[:, np.newaxis]
        Y_time_test = np.array([y[0] for y in Y_test])[:, np.newaxis]
        Y_extreme_test = np.array([y[1] for y in Y_test])[:, np.newaxis]
        
        self.make_predictor(X_crypto_train, X_crypto_test, Y_time_train, Y_time_test, 'model_time', cycles_t, load_model_t)
        self.make_predictor(X_crypto_train, X_crypto_test, Y_extreme_train, Y_extreme_test, 'model_extreme', cycles_e, load_model_e)

    def loop(self, window):

        while True:
            try:
                time_start = time.perf_counter()

                names = self.database.get_names()
                
                self.create_models(names, window, 2, True, 2, True)

                self.logger.log(f"{self.name}")
                
                time_end = time.perf_counter()
                print(time_end - time_start)
                sleep(max(0, self.timeout - (time_end - time_start)))
            except Exception as e:
                self.logger.log(str(e))
                sleep(self.timeout)


if __name__ == '__main__':
    trainer = Trainer()
    names = Database().get_names()
    trainer.create_models(names, 50, 0, True, 0, True)