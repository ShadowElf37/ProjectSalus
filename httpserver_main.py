from requisitioned_httpserver import Server
import os
import sys

print('Starting %s...' % __file__)
s = Server()
os.execl(__file__, *sys.argv)
s.run()
