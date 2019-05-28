#!/usr/bin/env python3

from sys import argv
from .env import EnvReader

env = EnvReader("gitauth")

uname = env.get("GIT_USERNAME")

if argv[1] == "Username for 'https://github.com': ":
    print(uname)
elif argv[1] == "Password for 'https://{}@github.com': ".format(uname):
    print(env.get("GIT_PASSWORD"))
else: exit(1)
