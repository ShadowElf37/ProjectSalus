from config import get_config
import pickle

config = get_config('persistent')

class PersistentThing:
    def __init__(self, name, default, eachwrite=False):
        self.name = name
        self.eachwrite = eachwrite
        self.fname = "{}/{}.dat".format(config.get('directory'), name)
        self.value = default
        try:
            self.fh = open(self.fname, "rb+")
            self.read()
        except FileNotFoundError:
            self.fh = open(self.fname, "wb+")
            self.write()

    def __del__(self):
        self.write()
        self.fh.close()

    def get(self):
        return self.value

    def set(self, value, *args):
        self.value = value
        self.autowrite()

    def read(self):
        self.fh.seek(0)
        try:
            self.value = pickle.load(self.fh)
        except EOFError:
            pass

    def autowrite(self):
        if self.eachwrite:
            self.write()

    def write(self):
        self.fh.seek(0)
        self.fh.truncate()
        pickle.dump(self.value, self.fh)

class PersistentDict(PersistentThing):
    def __init__(self, name, eachwrite=False):
        super().__init__(name, {}, eachwrite)

    def get(self, key, default=None):
        return self.value.get(key, default)

    def set(self, key, value):
        self.value[key] = value
        self.autowrite()

    def items(self):
        return self.value.items()

    def find(self, condition):
        try:
            return next(filter(condition, self.items()))
        except StopIteration:
            return None

    def delete(self, key):
        del super().get()[key]
        self.autowrite()
