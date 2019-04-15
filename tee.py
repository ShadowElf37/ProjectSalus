import sys
class Tee:
    def __init__(self, name, mode="a+"):
        self.file = open(name, mode)
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
    def __del__(self):
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        self.file.close()
    def write(self, data):
        self.file.write(data)
        self.stdout.write(data)
        self.stderr.write(data)
    def flush(self):
        self.file.flush()
