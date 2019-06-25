from server.server import Server
import os.path as op
from server.tee import *
from datetime import datetime
from server.config import get_config
import psutil

config = get_config("main")
psutil.cpu_percent()

logfile = open(op.join(
        op.dirname(op.abspath(__file__)),
        'logs',
        '{}.log'.format(datetime.now().strftime("%Y-%m-%d %H.%M.%S"))), "a", 1)

BUFFER = io.StringIO()
tees = (OutTee(logfile, BUFFER), ErrTee(logfile, BUFFER))

print('Starting %s...' % __file__)
s = Server(stdout_buffer=BUFFER, port=config.get("port"), host='localhost')
s.run()
logfile.close()
print('Server shut down gently.')
