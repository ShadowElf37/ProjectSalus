from server.server import Server
import os.path as op
from server.tee import *
from datetime import datetime
import server.config

# Obviously change these backslashes for Linux
logfile = open(op.join(
        op.dirname(op.abspath(__file__)),
        'logs',
        '{}.log'.format(datetime.now().strftime("%Y-%m-%d %H.%M.%S"))), "a", 1)
tees = (OutTee(logfile), ErrTee(logfile))

print('Starting %s...' % __file__)
s = Server()
server.config.SERVER = s
s.run()
logfile.close()
