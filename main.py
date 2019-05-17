#!/usr/bin/env python3
from subprocess import Popen
import sys
import os

import importlib.util as iutil
assert iutil.find_spec('selenium'), iutil.find_spec('bs4')
print('Library check passed.')

here = os.path.dirname(os.path.realpath(__file__))
os.chdir(here)
tomake = 'logs', 'data', 'config', 'web/assets'
for folder in tomake:
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
