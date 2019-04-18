import json

CONFIG_DIR = './config'
FMT_STR = '%s/{}.json' % CONFIG_DIR

class Config:
    def __init__(self, name: str):
        self.fh = open(FMT_STR.format(name), 'r+')
        self.name = name
        self.data = json.load(self.fh)
        if not isinstance(self.data, dict):
            raise ValueError("Top level JSON should always be a dictionary!")

    def get(self, key):
        return self.data.get(str(key), None)

    def dump(self):
        json.dump(self.data, self.fh)

    def __getattr__(self, item):
        return self.get(item)

    def __setattr__(self, k, v):
        self.data[k] = v

    def __del__(self):
        self.dump()
        self.fh.close()

def get_config(name):
    return Config(name)
