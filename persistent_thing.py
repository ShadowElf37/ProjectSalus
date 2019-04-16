from config import get_config
import pickle

config = get_config('persistent')

class PersistentThing:
    def __init__(self, name, default, eachwrite=False):
        self.name = name
        self.eachwrite = eachwrite
        self.fname = "{}/{}.dat".format(config.get('directory'), name)
        try:
            self.fh = open(self.fname, "rb+")
            self.read()
        except FileNotFoundError:
            self.fh = open(self.fname, "wb+")
            self.value = default
            self.write()
    def __del__(self):
        self.write()
        self.fh.close()
    def get(self):
        return self.value   
    def set(self, value):
        self.value = value
        self.autowrite()
    def read(self):
        self.fh.seek(0)
        self.value = pickle.load(self.fh)
    def autowrite(self):
        if eachwrite:
            self.write()
    def write(self):
        self.fh.seek(0)
        self.fh.truncate()
        pickle.dump(self.value, self.fh)

class PersistentDict(PersistentThing):
    def __init__(self, name, eachwrite=False):
        super().__init__(name, {}, eachwrite)
    def get(self, key, default=None):
        return super().get().get(key, default)
    def set(self, key, value):
        super().get()[key] = value
        self.autowrite()
    def delete(self, key):
        del super().get()[key]
        self.autowrite()
