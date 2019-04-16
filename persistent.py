from config import get_config
import pickle

config = get_config('persistent')

class PersistentDict:
    def __init__(self, name, default):
        self.name = name
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
        self.update()
    def read(self):
        self.fh.seek(0)
        self.value = pickle.load
    def write(self):
        self.fh.seek(0)
        self.fh.truncate()
        pickle.dump(self.value, self.fh)
