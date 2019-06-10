import json
import os

CONFIG_DIR = '../config'
if not os.path.isdir(CONFIG_DIR):
    CONFIG_DIR = './config'
    assert os.path.isdir(CONFIG_DIR), '__main__ is in a bad location - move it to Salus or Salus/server and try again.'

FMT_STR = '%s/{}.json' % CONFIG_DIR


class ConfigCache:
    def __init__(self):
        self.configs = []

    def reload(self):
        for c in self.configs:
            c.reload()

CONFIG_CACHE = ConfigCache()

import os.path
class Config:
    def __init__(self, name: str):
        self.fh = open(FMT_STR.format(name), 'r+')
        self.name = name
        self.data = json.load(self.fh)
        if not isinstance(self.data, dict):
            raise ValueError("Top level JSON should always be a dictionary!")

    def get(self, key):
        return self.data.get(str(key), None)

    def reload(self):
        self.__init__(self.name)

    # To whom it may concern: self.fh is opened with r+. This means append. Call seek(0) and truncate() before dumping data. Thanks. Also, these configs are supposed to be read-only rn. Dynamic config editing only leads to pain. Thanks again, Alwinfy
    #def __del__(self):
        #self.fh.close()


def get_config(name):
    return Config(name)
