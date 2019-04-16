from server import Server
import os.path as op
import sys
from tee import *
from datetime import datetime
from cache import FileCache

# Obviously change these backslashes for Linux
logfile = open("{here}\\logs\\{date}.log".format( \
    here=op.dirname(op.abspath(__file__)), \
    date=datetime.now().strftime("%Y-%m-%d %H.%M.%S")), "a", 1)
tees = (OutTee(logfile), ErrTee(logfile))

print('Starting %s...' % __file__)
s = Server()
s.run()
logfile.close()