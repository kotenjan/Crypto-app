from mimetypes import init
import random
import numpy as np
from sortedcontainers import SortedDict as sd
import json
from utils.database import Database


# Class attempts to find the best configuration based on past predictions evaluated in Interval class
class Genetic:

    def __init__(self, names):

        self.price_lo = -4
        self.price_hi = 4
        self.time_lo = -400
        self.time_hi = 400
        self.min_threshold = 0
        self.predictions = self.get_datasets(names)

    # loading of the file with all evaluated predictions
    def get_dataset(self, name):
        with open(f'/workspace/data/interval_{name.lower()}.json', 'r') as file:
            data = np.array(json.load(file), dtype=float)
        return data

    def save_as_json(self, data):

        data = [ (a, list(np.array(b, dtype=str))) for a,b in data ]

        with open(f'/workspace/data/config.json', 'w') as file:
            json.dump(data, file)

    def get_datasets(self, names):
        return [self.get_dataset(name) for name in names]

    # heuristic function, which will evaluate given configuration
    def cash_up(self, config):

        transactions = 0.0
        
        rising = config[0]
        sinking = config[1]
        time_buy_rising = config[2]
        time_buy_sinking = config[3]
        time_sell_rising = config[4]
        time_sell_sinking = config[5]

        stat = list()

        for prediction in self.predictions:

            cash =  1.0
            bought = False
            bought_value = 0.0

            # For better orientation there are used strings instead of numbers
            for interval in prediction:
                    
                growth = interval[0]
                duration = interval[1]
                current_price = interval[2]
                advice = 'wait'

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

                if not bought and advice == 'buy':
                    bought = True
                    bought_value = current_price
                    deposited = cash
                    #print(f'BUY: {list(interval)}, CASH: {cash}, CURRENT_PRICE: {current_price}, BOUGHT_VALUE: {bought_value}, DEPOSITED: {deposited}')
                if bought and advice == 'sell':
                    bought = False
                    transactions += 1
                    cash = (current_price / bought_value) * deposited
                    #print(f'SELL: {list(interval)}, CASH: {cash}, CURRENT_PRICE: {current_price}, BOUGHT_VALUE: {bought_value}, DEPOSITED: {deposited}')

            stat.append(round(cash - 1, 4))

        return min(stat), (transactions, tuple(stat))

    # mutation of each element
    def update(self, low, high, current, gain):

        gain = max(0.2, 0.1 - gain)

        curr_lo = current + gain * (low-current)
        curr_hi = current + gain * (high-current)
        return round((curr_hi-curr_lo)*random.random() + curr_lo, 2)

    def get_growth_threshold(self, current, gain):

        return self.update(self.price_lo, self.price_hi, current, gain)

    def get_interval_threshold(self, current, gain):

        return self.update(self.time_lo, self.time_hi, current, gain)

    # mutation
    def modify_random_state(self, state):

        gain = state[0][0]
        config = state[1]

        return np.array([
            self.get_growth_threshold(config[0], gain),
            self.get_growth_threshold(config[1], gain),
            self.get_interval_threshold(config[2], gain),
            self.get_interval_threshold(config[3], gain),
            self.get_interval_threshold(config[4], gain),
            self.get_interval_threshold(config[5], gain),
        ])

    def create_population(self, current_config_arr, all_count, top_count):

        population = sd()
        for current_config in current_config_arr:
            for _ in range(all_count):
                config = self.modify_random_state(current_config)
                gain, transactions = self.cash_up(config)
                if gain > 0:
                    population[(gain, transactions)] = config

        return sd(population.items()[-top_count:])

    # crossing
    def cross_elements(self, x, y):

        state = np.random.rand(len(x))
        element = x*state + y*(1-state)
        return np.array([round(x, 2) for x in element])

    def mutate_population(self, current_rotations_arr, top_count):

        population = sd()
        for x in current_rotations_arr:
            for y in current_rotations_arr:
                config = self.cross_elements(x[1], y[1])
                gain, transactions = self.cash_up(config)
                if gain > 0:
                    population[(gain, transactions)] = config

        return sd(population.items()[-top_count:])

    # configuration is being saved periodically and can be loaded if necessary
    def load_configs(self):
        with open(f'/workspace/data/config.json', 'r') as file:
            return np.array([ np.array(x[1], dtype=float) for x in json.load(file)])

    # Runs specified number of generations
    # each generation is mutatet and then crossed
    def get_purchase_config(self, population_count, top_count, generations_before_exit, load_configs=False):
        
        cycle_count = 0
        population = sd()
        if load_configs:
            configs = self.load_configs()
        else:
            configs = np.array([[0.69, -0.8, -96.7, 57.43, 281.61, 15.63]])

        for config in configs:
            gain, transactions = self.cash_up(config)
            population[(gain, transactions)] = config

        best_item = population.items()[-1]
        min_gain = min(best_item[0][1][1])
        if min_gain > self.min_threshold:
            self.min_threshold = round(min_gain, 2)
        
        while cycle_count < generations_before_exit:

            population = sd(population.items()[-top_count:])

            mutated = self.create_population(population.items(), int(population_count/top_count), top_count)
            crossed = self.mutate_population(population.items(), top_count)

            population.update(mutated)
            population.update(crossed)

            cycle_count += 1

            best_item = population.items()[-1]
            min_gain = min(best_item[0][1][1])
            if min_gain > self.min_threshold:
                self.min_threshold = round(min_gain, 2)

            print(cycle_count, best_item)
            self.save_as_json(list(population.items()))

        return population.items()[-top_count:]

if __name__ == '__main__':

    genetic = Genetic(Database.get_names())
    genetic.get_purchase_config(100, 25, 1000)
