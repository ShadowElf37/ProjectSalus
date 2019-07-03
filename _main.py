from server.server import Server
import os.path as op
from server.tee import *
from datetime import datetime
from server.config import get_config
import multiprocessing as mp

mp.set_start_method('spawn')
mp.freeze_support()

config = get_config("main")

logfile = open(op.join(
        op.dirname(op.abspath(__file__)),
        'logs',
        '{}.log'.format(datetime.now().strftime("%Y-%m-%d %H.%M.%S"))), "a", 1, errors='replace')

BUFFER = io.StringIO()
tees = (OutTee(logfile, BUFFER), ErrTee(logfile, BUFFER))

print('Starting %s...' % __file__)
s = Server(stdout_buffer=BUFFER, port=config.get("port"), host='localhost')
s.run()
logfile.close()
print('Server shut down gently.')
