#!/usr/bin/env python3
from subprocess import Popen
import sys
import os

here = os.path.dirname(os.path.realpath(__file__))
os.chdir(here)

while True:
    process = Popen([sys.executable, '_main.py'],
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr)
    process.wait()
    if process.returncode == 37:
        process.kill()
        print('REBOOTING')
        continue
    break
