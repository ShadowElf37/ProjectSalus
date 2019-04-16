from subprocess import *
from sys import exit, executable
import os
import sys

class Process:
    def __init__(self, py_file):
        self.file = py_file
        self.code = open(py_file).read()

    def start(self):
        exec(self.code)

    def reboot(self):
        os.execl(__file__, *sys.argv)

    def update(self):
        try:
            return check_output(['git', 'pull'])
        except CalledProcessError as e:
            return 'Error:', e.stderr


def reboot():
    Popen([executable, __file__], cwd=os.getcwd())
    exit(0)

if __name__ == "__main__":
    reboot()
