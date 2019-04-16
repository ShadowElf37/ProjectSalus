from server import Server
import os.path as op
import sys
from tee import *
from datetime import datetime
import client

# Obviously change these backslashes for Linux
logfile = open(op.join(
        op.dirname(op.abspath(__file__)),
        'logs',
        '{}.log'.format(datetime.now().strftime("%Y-%m-%d %H.%M.%S"))), "a", 1)
tees = (OutTee(logfile), ErrTee(logfile))

print('Starting %s...' % __file__)
s = Server()
s.run()
logfile.close()
