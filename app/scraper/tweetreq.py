from datetime import datetime as dt
from datetime import timedelta as td
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from threading import Thread
import random
from utils.database import Database
from utils.logger import Logger


# Downloading tweets from twitter
class TweetReq(object):

    fail_bit = False

    def __init__(self, timeout, short_timeout):
        self.general_url = 'https://twitter.com/search?q='
        self.page_load_timeout = 100
        self.max_scroll_attempt = 2000
        self.max_read_attempt = 3
        self.short_timeout = short_timeout
        self.timeout = timeout
        self.scroll_height = 300
        self.name = 'tweet'
        self.database = Database()
        self.logger = Logger()


    # get just the essential data to identify unique tweet that is not an ad
    def parse_tweet(self, card):

        try:
            postdate = card.find_element(By.XPATH, './/time').get_attribute('datetime')
        except:
            postdate = None

        try:
            promoted = card.find_element(By.XPATH, './/div[2]/div[2]/[last()]//span').text == "Promoted"
        except:
            promoted = None
        
        try:
            element = card.find_element(By.XPATH, './/a[contains(@href, "/status/")]')
            tweet_url = element.get_attribute('href')
        except:
            tweet_url = None

        tweet = (postdate, tweet_url, promoted)
        
        return tweet

    # Selenium is used
    def get_driver(self):
        
        options = Options()    
        options.add_argument('--no-sandbox')
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--profile-directory=Default')

        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(100)
        return driver

    def open_page(self, driver, since, hashtag):

        general_url = 'https://twitter.com/search?q='
        
        end_date = dt.strftime(since + td(days=2), 'until%%3A%Y-%m-%d')
        start_date = dt.strftime(since - td(days=2), 'since%%3A%Y-%m-%d%%20')

        hash_tags = "(%23" + hashtag + ")%20"
        path = general_url + hash_tags + start_date + end_date + '&src=typed_query&f=live'

        driver.get(path)

    # If the page can't be scrolled after several attempts, the scraping stops
    def scroll(self, driver):

        scroll_attempt = 0

        while True:
            sleep(random.uniform(0.5, 1.5))
            last_position = driver.execute_script("return window.pageYOffset;")
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            curr_position = driver.execute_script("return window.pageYOffset;")
            if last_position == curr_position:
                scroll_attempt += 1
                if scroll_attempt >= 60:
                    print('FAIL')
                    return False
                else:
                    sleep(random.uniform(0.5, 1.5))  # attempt another scroll
            else:
                return True

    # Returns number of tweets per each minute
    def count_tweets(self, tweets):

        data = dict()

        for tweet in tweets:
            tweet_date = dt.strptime(tweet[0], '%Y-%m-%dT%H:%M:%S.000Z')
            rounded_time = tweet_date - td(seconds=tweet_date.second)
            if rounded_time not in data:
                data[rounded_time] = 1
            else:
                data[rounded_time] += 1

        return data

    def get_tweets(self, driver):

        tweets = set()

        while True:
            sleep(random.uniform(0.5, 1.5))
            page_cards = driver.find_elements(By.XPATH, '//article[@data-testid="tweet"]')
            for card in page_cards:
                tweet = self.parse_tweet(card)
                if tweet and tweet not in tweets:
                    tweets.add(tweet)
                    print(tweet[0], tweet[1])
            
            if not self.scroll(driver):
                return self.count_tweets(tweets)            

    # The tweets are not saved in the database since they are not being used in the final solution
    def scrape(self, since, hashtag):
        
        driver = self.get_driver()
        
        self.open_page(driver=driver, since=since, hashtag=hashtag)
        print(self.get_tweets(driver))
        
        driver.close()

    def loop(self):

        while not TweetReq.fail_bit:
            start = time.perf_counter()

            names = self.database.get_names()

            start_time = dt.now() - td(hours=1)
            threads = [Thread(target=self.scrape, args=(start_time, name)) for name in names]
            for thread in threads: thread.start()
            for thread in threads: thread.join()
            self.logger.log(f"{start_time} {self.name}")
                
            end = time.perf_counter()
            sleep(max(0, self.timeout - (end - start)))


if __name__ == '__main__':
    tweet = TweetReq(60, 30)
    tweet.loop()
