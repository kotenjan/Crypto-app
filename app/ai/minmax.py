import numpy as np
from scipy.signal import argrelextrema
from scipy.ndimage import gaussian_filter1d


# This Class has methods that find local extremes in given dataset
class Minmax:
    
    def __init__(self, window=15):
        self.window = window

    def fill_edges(self, minima, maxima, first_val, last_val):
        
        minima = set(minima)
        minima.update([first_val, last_val])
        maxima = set(maxima)
        maxima.update([first_val, last_val])
        
        return sorted(minima), sorted(maxima)

    def select_local_extremes(self, arr):
        
        maxima = argrelextrema(arr, np.greater, mode='wrap')[0]
        minima = argrelextrema(arr, np.less, mode='wrap')[0]

        minima, maxima = self.fill_edges(minima, maxima, 0, arr.size - 1)
        
        return minima, maxima

    def create_pairs(self, arr):
        a = np.array(arr[:-1])
        b = np.array(arr[1:]) + 1
        return np.stack((a, b), axis=-1)

    def find_minmax_in_range(self, range, arr, func):
        interval = arr[np.arange(start = range[0], stop=range[1])]
        interval_minmax = func(interval)
        return range[0] + interval_minmax

    # First the gaussian filter is applied to the original dataset
    # Then local extremes are selected 
    # A local minimum in original dataset is found between two local maximums in the filtered dataset
    def find_extremes(self, arr, add_artificial_edge_extremes=True):
        
        gaussian_array = gaussian_filter1d(arr, self.window)
        minima, maxima = self.select_local_extremes(gaussian_array)

        minima_pair = self.create_pairs(minima)
        maxima_pair = self.create_pairs(maxima)

        minima = [self.find_minmax_in_range(pair, arr, np.argmin) for pair in maxima_pair]
        maxima = [self.find_minmax_in_range(pair, arr, np.argmax) for pair in minima_pair]

        extremes = sorted(set.union(set(minima), set(maxima)))

        if add_artificial_edge_extremes == False:
            return extremes[1:-1], gaussian_array

        return extremes, gaussian_array
