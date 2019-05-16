import sys
import io

class UnifiedTee:
    def __init__(self, handle):
        self.file = handle
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.buffer = io.StringIO()
        sys.stdout = self
        sys.stderr = self
    def __del__(self):
        sys.stdout = self.stdout
        sys.stderr = self.stderr
    def write(self, data):
        self.file.write(data)
        self.stdout.write(data)
        self.buffer.write(data)
    def flush(self):
        self.file.flush()

class OutTee:
    def __init__(self, handle, buffer=io.StringIO()):
        self.file = handle
        self.stdout = sys.stdout
        self.buffer = buffer
        sys.stdout = self
    def __del__(self):
        sys.stdout = self.stdout
    def write(self, data):
        self.file.write(data)
        self.stdout.write(data)
        self.buffer.write(data)
    def flush(self):
        self.file.flush()

class ErrTee:
    def __init__(self, handle, buffer=io.StringIO()):
        self.file = handle
        self.stderr = sys.stderr
        self.buffer = buffer
        sys.stderr = self
    def __del__(self):
        sys.stderr = self.stderr
    def write(self, data):
        self.file.write(data)
        self.stderr.write(data)
        self.buffer.write(data)
    def flush(self):
        self.file.flush()
