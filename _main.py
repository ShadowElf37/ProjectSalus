from httpserver.server import Server
import os.path as op
from httpserver.tee import *
from datetime import datetime
import httpserver.config

logfile = open(op.join(
        op.dirname(op.abspath(__file__)),
        'logs',
        '{}.log'.format(datetime.now().strftime("%Y-%m-%d %H.%M.%S"))), "a", 1)

BUFFER = io.StringIO()
tees = (OutTee(logfile, BUFFER), ErrTee(logfile, BUFFER))

print('Starting %s...' % __file__)
s = Server(stdout_buffer=BUFFER)
s.run()
logfile.close()
print('Server shut down gently.')