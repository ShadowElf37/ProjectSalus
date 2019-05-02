import sys

class OutTee:
    def __init__(self, handle):
        self.file = handle
        self.stdout = sys.stdout
        sys.stdout = self
    def __del__(self):
        sys.stdout = self.stdout
    def write(self, data):
        self.file.write(data)
        self.stdout.write(data)
    def flush(self):
        self.file.flush()

class ErrTee:
    def __init__(self, handle):
        self.file = handle
        self.stderr = sys.stderr
        sys.stderr = self
    def __del__(self):
        sys.stderr = self.stderr
    def write(self, data):
        self.file.write(data)
        self.stderr.write(data)
    def flush(self):
        self.file.flush()
