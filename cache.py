from _io import TextIOWrapper

class FileCache:
    ALL = object()
    def __init__(self):
        self.cache = dict()

    def read(self, f, binary=False):
        ff = self.cache.get(f)
        if ff is None:
            self.cache[f] = open(f, 'rb' if binary else 'r').read()
        return ff

    def open(self, f, mode='w'):
        ff = self.cache.get(f)
        if ff is None:
            self.cache[f] = open(f, mode)
        return ff

    def write(self, f, s):
        ff = self.cache.get(f)
        if ff is None:
            raise IOError('Requested file is not opened.')
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
