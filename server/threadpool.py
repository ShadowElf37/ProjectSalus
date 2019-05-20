from threading import *
from server.config import get_config
from time import sleep

config = get_config('threads')

class Poolsafe:
    def __init__(self, f, *args, **kwargs):
        self.f = f
        self.args = args
        self.kwargs = kwargs
        self.r = '!@#$%none'  # None is bad because functions might actually return None and we want to see that

    @staticmethod
    def await_all(*ps):
        while any(p.r == '!@#$%none' for p in ps):
            sleep(0.0001)

    def wait(self):
        while self.r == '!@#$%none':
            sleep(0.0001)

    def call(self):
        self.r = self.f(*self.args, **self.kwargs)

    def read(self):
        return self.r

    def reset(self):
        self.r = '!@#$%none'


class Pool:
    def __init__(self, threadcount):
        self.condition = Condition()
        self.queue = []
        self.threads = [Fish(self.condition, self.queue) for _ in range(threadcount)]

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

    def push(self, reqtuple):
        self.pushf(None, *reqtuple)

    def pushf(self, f, *args, **kwargs):
        with self.condition:
            self.queue.insert(0, (f,) + args + ((kwargs,) if kwargs else ()))
            self.condition.notify()

    def pushps(self, ps):
        self.pushf(ps)

    def pushps_multi(self, *ps):
        for p in ps:
            self.pushps(p)

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

            if type(r[0]) is Poolsafe:
                r[0].call()
                continue

            if r[0] is not None:
                r[0](*r[1:-1], **r[-1])
                continue

            server, request, client_address = r[1:]
            server.finish_request(request, client_address)
            server.shutdown_request(request)
            self.busy = False

class RWLockMixin:
    """Make any getattr access rw-locked."""
    def __init__(self):
        self._read_ready = Condition(RLock())
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
        if not item.startswith("_"):
            with self._read_ready:
                while self._readers > 0:
                    self._read_ready.wait()
                object.__setattr__(self, item, val)
        else: object.__setattr__(self, item, val)
    def __delattr__(self, item):
        if not item.startswith("_"):
            with self._read_ready:
                while self._readers > 0:
                    self._read_ready.wait()
                object.__delattr__(self, item)
        else: object.__delattr__(self, item)

