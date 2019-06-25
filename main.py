#!/usr/bin/env python3
from subprocess import Popen
import sys
import os

from importlib.util import find_spec

DEPENDENCIES = ('requests', 'bs4', 'cryptography', 'git', 'psutil')

assert all(map(find_spec, DEPENDENCIES)),\
    'Missing libraries are required to continue. Check to make sure you have {} installed.'.format(', '.join(DEPENDENCIES[:-1]).title()+', and '+DEPENDENCIES[-1].title())
print('Library check passed.')

HERE = os.path.dirname(os.path.realpath(__file__))
os.chdir(HERE)
for folder in ('logs', 'data', 'config', 'web/assets'):
    try:
        os.mkdir(folder)
    except FileExistsError:
        pass

assert os.path.exists('.env'), 'Toplevel env file not found.'

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
