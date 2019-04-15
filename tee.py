import sys
class Tee(object):
    def __init__(self, name, mode="a"):
        self.file = open(name, mode)
        self.stdout = sys.stdout
        sys.stdout = self
    def __del__(self):
        sys.stdout = self.stdout
        self.file.close()
    def write(self, data):
        self.file.write(data)
        self.stdout.write(data)
    def fileno(self):
        return self.stdout.fileno
    def flush(self):
        self.file.flush()
