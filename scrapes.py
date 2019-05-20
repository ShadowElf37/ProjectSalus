from server.threadpool import Poolsafe, Pool
from server.timedworker import Updater, UpdateManager
from scrape import *
from time import time, sleep

ScrapingPool = Pool(20)
ScrapingPool.launch()

blackbaud = BlackbaudScraper()
blackbaud.login('ykey-cohen', 'Yoproductions3', 't')

DIRECTORY = blackbaud.directory()

ScrapingManager = UpdateManager(ScrapingPool)
# ScrapingManager.register(Poolsafe())

print('Scrape managers initialized.')