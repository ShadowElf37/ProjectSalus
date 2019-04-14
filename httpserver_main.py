from requisitioned_httpserver import Server
import os
import sys

py = sys.executable

print('Starting %s...' % __file__)
s = Server()
s.run()
