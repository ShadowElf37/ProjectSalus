import json
from os.path    import isdir
from env        import EnvReader

DEFAULT_LOCATIONS = ('../config', 'config')
FMT_STR = '{}/{}.json'

class ConfigCache:
    def __init__(self):
        self.configs = []

    def reload(self):
        for c in self.configs:
            c.reload()

CONFIG_CACHE = ConfigCache()

import os.path
class Config:
    def __init__(self, name: str, location: str=None):
        try: conf_dir = next(filter(ispath,
                DEFAULT_LOCATIONS if location is None else location))
        except StopIteration:
            raise ValueError("Can't find suitable config directory!")
        self.fh = open(FMT_STR.format(name), 'r+')
        self.name = name
        self.reload()

    def get(self, key):
        return self.data.get(str(key), None)

    def reload(self):
        self.data = json.load(self.fh)
        if not isinstance(self.data, dict):
            raise ValueError("Top level JSON should always be a dictionary!")

    # To whom it may concern: self.fh is opened with r+. This means append. Call seek(0) and truncate() before dumping data. Thanks. Also, these configs are supposed to be read-only rn. Dynamic config editing only leads to pain. Thanks again, Alwinfy
    #def __del__(self):
        #self.fh.close()
    @staticmethod
    def verify_dir(directory: str) -> bool:
        return ispath(directory)


def get_config(name):
    return Config(name)
