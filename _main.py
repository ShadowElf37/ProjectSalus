from server import Server
import os.path as op
import sys
from tee import Tee
from datetime import datetime

# Obviously change these backslashes for Linux
tee = Tee("{here}\\logs\\{date}.log".format( \
    here=op.dirname(op.abspath(__file__)), \
    date=datetime.now().strftime("%Y-%m-%d %H;%M;%S")))

print('Starting %s...' % __file__)
s = Server()
s.run()
