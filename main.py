from subprocess import Popen
import sys

while True:
    process = Popen(['python', '_main.py'], stdout=sys.stdout, stderr=sys.stderr, stdin=sys.stdin)
    process.wait()
    if process.returncode == 37:
        process.kill()
        print('REBOOTING')
        continue
    break