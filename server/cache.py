from _io import TextIOWrapper
import os.path as op
from server.config import get_config
from mimetypes import guess_type, add_type
from fnmatch import fnmatch
from time import time, sleep
from threading import Thread


CONTENT_TYPE = {
    'html': 'text/html',
    'htm': 'text/html',
    'css': 'text/css',
    'js': 'application/javascript',
    'txt': 'text/plain',
    'xml': 'text/xml',
    'ttf': 'font/ttf',
    'mp3': 'audio/mpeg',
    'wav': 'audio/x-wav',
    'ogg': 'audio/ogg',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'gif': 'image/gif',
    'bmp': 'image/bmp',
    'svg': 'image/svg+xml',
    'mp4': 'video/mp4',
    'mov': 'video/quicktime',
    'h265': 'video/h265',
    'avi': 'video/h265',
}

for k,v in CONTENT_TYPE.items():
    add_type(v, ('.' if k[0] is not '.' else '')+k)

def guess_mime(path):
    r = guess_type(path)[0]
    return r if r is not None else 'application/octet-stream'


class Updater:
    def __init__(self, name, updatefunc, update_condition=lambda: True):
        # If update_condition is not set manually, the TimingCache will handle it based on expiry duration
        self.name = name
        self.f = updatefunc
        self.condition = update_condition

    def poll(self):
        return self.condition()

    def renew(self):
        return self.f()

class TimingCache:
    def __init__(self):
        self._cache = {}
        self.durations = {}
        self.updaters = []
        self.update_thread = Thread(target=self.update_loop, daemon=True)

    def init(self):
        self.update_thread.start()

    def update_loop(self):
        while True:
            for update in self.updaters.copy():
                f = self.fetch(update.name)
                if f is None and update.poll():
                    self._cache[update.name] = update.renew()
                    self.durations[update.name][1] = time()
                elif f == False:
                    self.updaters.remove(update)
            sleep(5)


    def cache(self, name, text, min_duration=3600, updater:Updater=None):
        self._cache[name] = text
        self.durations[name] = (min_duration, time())
        if updater: self.updaters.append(updater)

    def fetch(self, name):
        d, t = self.durations.get(name, (-1, -1))
        if d == t == -1:
            return False

        if d*60 + t <= time():
            return None
        return self._cache[name]

    def clear(self, name):
        del self.durations[name]
        del self._cache[name]


class FileCache:
    ALL = object()
    def __init__(self):
        self.cache = dict()

    def read(self, f, binary=True, cache=True):
        ff = self.cache.get(f)
        of = f
        tfolder = None
        m = guess_mime(f)
        for t, dir in get_config('locations').data.items():
            if fnmatch(t, m):
                tfolder = dir
        # tfolder = get_config('locations').get(op.splitext(f)[1])
        f = 'web'+f
        if ff is None:
            # recursive search      while op.split(f)[0] != '/':
            try:
                ff = open(f, 'rb' if binary else 'r').read()
            except FileNotFoundError:
                pass
            # recursive search      f = '/'.join(op.split(f)[0].split('/')[:-1]) + '/' + op.split(f)[1]

            if tfolder:
                # print('web/assets' + tfolder + '/' + op.split(of)[1])
                try:
                    ff = open('web/assets' + tfolder + '/' + op.split(of)[1], 'rb' if binary else 'r').read()
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
