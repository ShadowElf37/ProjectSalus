from _io import TextIOWrapper
import os.path as op
from server.config import get_config

class FileCache:
    ALL = object()
    def __init__(self):
        self.cache = dict()

    def read(self, f, binary=True, cache=True):
        ff = self.cache.get(f)
        of = f
        tfolder = get_config('locations').get(op.splitext(f)[1])
        f = 'web'+f
        if ff is None:
            while op.split(f)[0] != '/':
                # print(op.split(f))
                try:
                    ff = open(f, 'rb' if binary else 'r').read()
                except FileNotFoundError:
                    pass
                f = '/'.join(op.split(f)[0].split('/')[:-1]) + '/' + op.split(f)[1]

            if tfolder:
                # print('web/assets' + tfolder + '/' + op.split(of)[1])
                try:
                    ff = open('web/assets'+tfolder + '/' + op.split(of)[1], 'rb' if binary else 'r').read()
                except FileNotFoundError:
                    pass

        if cache:
            self.cache[of] = ff
        return ff

    def open(self, f, mode='w'):
        ff = self.cache.get(f)
        if ff is None:
            self.cache[f] = ff = open('web'+f, mode)
        return ff

    def write(self, f, s):
        ff = self.cache.get(f)
        if ff is None:
            raise IOError('Requested file is not open.')
        ff.write(s)

    def reload(self, f="_ALL"):
        if f == "_ALL":
            self.close()
            self.cache = dict()
        else:
            self.cache.get(f).close()

    def close(self):
        for f in self.cache.values():
            if isinstance(f, TextIOWrapper):
                f.close()

    def __enter__(self):
        ...

    def __exit__(self):
        self.close()

    def __del__(self):
        self.close()
