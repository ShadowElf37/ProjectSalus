from subprocess import *
from sys import exit
from os import getcwd

def update():
    try:
        return check_output(['git', 'pull'])
    except CalledProcessError as e:
        return 'Error:', e.stderr

def reboot():
    Popen(['python', 'main.py'], cwd=getcwd())
    exit(0)

if __name__ == "__main__":
    reboot()