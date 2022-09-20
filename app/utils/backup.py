from datetime import datetime as dt
from utils.database import Database
from utils.logger import Logger
import time
from time import sleep


# periodically save downloaded data to csv as backup
class Backup():

    def __init__(self, timeout, short_timeout):
        self.database = Database()
        self.logger = Logger()
        self.timeout = timeout
        self.short_timeout = short_timeout

    def save(self, names):
        sleep(self.short_timeout)
        self.database.select_all_from_and_fix_missing('vix',    'vix',    'ffill', replace_null=True, limit_area='inside', save_to_csv=True),
        self.logger.log('VIX SAVED')
        sleep(self.short_timeout)
        self.database.select_all_from_and_fix_missing('sap',    'sap',    'ffill', replace_null=True, limit_area='inside', save_to_csv=True),
        self.logger.log('S&P 500 SAVED')
        sleep(self.short_timeout)
        self.database.select_all_from_and_fix_missing('gold',   'gold',   'ffill', replace_null=True, limit_area='inside', save_to_csv=True),
        self.logger.log('GOLD SAVED')

        for name in names:
            sleep(self.short_timeout)
            self.database.select_all_from_and_fix_missing(name, 'trends', 'linear', replace_null=False, limit_area='inside', save_to_csv=True)
            self.logger.log(f'{name.upper()} TREND  SAVED')
            sleep(self.short_timeout)
            self.database.select_all_from_and_fix_missing(name, 'crypto', 'linear', replace_null=True, limit_area='inside', save_to_csv=True)
            self.logger.log(f'{name.upper()} CRYPTO SAVED')
    
    def loop(self):

        while True:
            try:
                time_start = time.perf_counter()

                names = self.database.get_names()
                
                self.save(names)

                time_end = time.perf_counter()
                sleep(max(0, self.timeout - (time_end - time_start)))
            except Exception as e:
                self.logger.log(str(e))
                sleep(self.short_timeout)

