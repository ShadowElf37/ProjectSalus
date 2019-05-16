from threading import *
from httpserver.config import get_config

config = get_config('threads')

class Pool:
    def __init__(self, threadcount):
        self.condition = Condition()
        self.queue = []
        self.threads = [Fish(self.condition, self.queue) for i in range(threadcount)]

    def launch(self):
        for t in self.threads:
            t.init_thread()

    def cleanup(self):
        for t in self.threads:
            t.terminate()
        with self.condition:
            self.condition.notifyAll()
        for t in self.threads:
            t.thread.join(config.get('cleanup-timeout'))

    def push(self, args):
        self.pushf(None, args)

    def pushf(self, f, args):
        with self.condition:
            self.queue.insert(0, tuple([f] + list(args)))
            self.condition.notify()

class Fish:
    def __init__(self, condition, queue):
        self.condition = condition
        self.queue = queue
        self.thread = Thread(target=self.mainloop, daemon=True)
        self.running = True
        self.busy = False

    def init_thread(self):
        self.thread.start()
    
    def terminate(self):
        self.running = False

    def alive(self):
        return self.thread.is_alive()

    def mainloop(self):
        while self.running:
            with self.condition:
                while True:
                    if not self.running: return
                    if self.queue:
                        r = self.queue.pop()
                        break
                    self.condition.wait()
            self.busy = True

            if r[0] is not None:
                r[0](*r[1:])
                continue

            server, request, client_address = r[1:]
            server.finish_request(request, client_address)
            server.shutdown_request(request)
            self.busy = False

class RWLockMixin:
    """Make any getattr access rw-locked."""
    def __init__(self):
        self._read_ready = Condition(Lock())
        self._readers = 0
    def __getattribute__(self, item):
        if not item.startswith("_"):
            with self._read_ready:
                self._readers += 1
            try:
                attr = object.__getattribute__(self, item)
            finally:
                with self._read_ready:
                    self._readers -= 1
                    if not self._readers:
                        self._read_ready.notifyAll()
            return attr
        return object.__getattribute__(self, item)
    def __setattr__(self, item, val):
        with self._read_ready:
            while self._readers > 0:
                self._read_ready.wait()
            object.__setattr__(self, item, val)
    def __delattr__(self, item):
        with self._read_ready:
            while self._readers > 0:
                self._read_ready.wait()
            object.__delattr__(self, item)
