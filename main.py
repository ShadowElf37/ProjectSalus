#!/usr/bin/env python3
from subprocess import Popen
import sys
import os

import importlib.util as imputil
assert imputil.find_spec('selenium'), imputil.find_spec('bs4')
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
