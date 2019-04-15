#!/usr/bin/env python3
from subprocess import Popen
import sys

while True:
    process = Popen([sys.executable, '_main.py'], \
        stdin=sys.stdin, \
        stdout=sys.stdout, \
        stderr=sys.stderr)
    process.wait()
    if process.returncode == 37:
        process.kill()
        print('REBOOTING')
        continue
    break
