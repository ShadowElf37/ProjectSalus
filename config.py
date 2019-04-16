
CONFIG_DIR = './conf'
FMT_STR = '%s/{}.cfg' % CONFIG_DIR

class Config:
    def __init__(self, name: str):
        self.fh = open(FMT_STR.format(name), 'r+')
        self.name = name
        self.data = {}
        for line in self.fh:
            line = line[:line.find('#')]
            if not line or line.iswhitespace():
                continue
            try:
                key, val = (t.strip() for t in line.strip().split(':', maxsplit=1))
            except ValueError:
                self.die("Got malformed syntax in {}".format(self.name))
            if val[0:2] == "[[":
                val = val[2:].split(",")
            self.data[key] = val
    def get(self, key):
        return self.data.get(str(key), None)
    def die(self, msg):
        raise ValueError(msg)
    def __del__(self):
        self.fh.close()

def get_config(name):
    return Config(name)
