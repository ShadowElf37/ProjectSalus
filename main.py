#!/usr/bin/env python3
from subprocess import Popen
import sys
import os

import importlib.util as imputil

DEPENDENCIES = ('requests', 'bs4', 'cryptography', 'git')

assert all(imputil.find_spec(i) for i in DEPENDENCIES),\
    'Missing libraries are required to continue. Check to make sure you have {} installed.'.format(', '.join(DEPENDENCIES[:-1]).title()+', and '+DEPENDENCIES[-1].title())
print('Library check passed.')

HERE = os.path.dirname(os.path.realpath(__file__))
os.chdir(HERE)
for folder in ('logs', 'data', 'config', 'web/assets'):
    try:
        os.mkdir(folder)
    except FileExistsError:
        pass

while True:
    process = Popen([sys.executable, '_main.py'],
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr)
    process.wait()
    if process.returncode == 37:
        process.kill()
        print('Rebooting.')
        continue
    elif process.returncode == 0:
        print('Shut down gracefully.')
        process.kill()
    break
