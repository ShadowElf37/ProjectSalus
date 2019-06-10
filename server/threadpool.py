from threading import *
from .config import get_config
from inspect import isfunction, ismethod

config = get_config('threads')

class Minisafe:
    def __init__(self, f, *args, **kwargs):
        self.f = f
        self.args = args
        self.kwargs = kwargs

    @staticmethod
    def find_minisafes(args):
        nargs = []
        for arg in args:
            if isinstance(arg, Minisafe):
                nargs.append(arg.call())
            else:
                nargs.append(arg)
        return nargs

    @staticmethod
    def find_minisafes_kw(kwargs):
        nkwargs = {}
        for k,v in kwargs.items():
            if isinstance(v, Minisafe):
                nkwargs[k] = v.call()
            else:
                nkwargs[k] = v
        return nkwargs

    def call(self):
        return self.f(*self.args, **self.kwargs)

CALLABLE = object()
class Poolsafe:
    NONCE = object()
    def __init__(self, f, *args, **kwargs):
        if not (isfunction(f) or ismethod(f)): raise TypeError('Poolsafe needs a function to run.')
        self.f = f
        self.args = args
        self.kwargs = kwargs
        self.r = Poolsafe.NONCE  # None is bad because functions might actually return None and we want to see that
        self.cond = Condition(Lock())
        self.after = []

    @staticmethod
    def await_all(*pses):
        it = iter(pses)
        ps = next(it, Poolsafe.NONCE)
        if ps is Poolsafe.NONCE:
            return
        with ps.cond:
            while ps.r is Poolsafe.NONCE:
                ps.cond.wait()
            Poolsafe.await_all(it)

    def wait(self):
        with self.cond:
            while self.r is Poolsafe.NONCE:
                self.cond.wait()
        return self.r

    def call(self):
        with self.cond:
            args = Minisafe.find_minisafes(self.args)
            kwargs = Minisafe.find_minisafes_kw(self.kwargs)
            self.r = self.f(*args, **kwargs)
            for f, args, kwargs in self.after:
                a = Minisafe.find_minisafes(self.args)
                k = Minisafe.find_minisafes_kw(self.kwargs)
                f(*a, **k)
            self.cond.notify_all()

    def read(self):
        return self.r

    def reset(self):
        with self.cond:
            self.r = Poolsafe.NONCE

    def on_completion(self, f, *args, **kwargs):
        self.after.append((f, args, kwargs))


class Pool:
    def __init__(self, threadcount):
        self.condition = Condition(Lock())
        self.queue = []
        self.threads = [Fish(self.condition, self.queue) for _ in range(threadcount)]

    def launch(self):
        for t in self.threads:
            t.init_thread()

    def cleanup(self):
        for t in self.threads:
            t.terminate()
        with self.condition:
            self.condition.notify_all()
        for t in self.threads:
            t.thread.join(config.get('cleanup-timeout'))

    def push(self, reqtuple):
        self.pushf(None, *reqtuple)

    def pushf(self, f, *args, **kwargs):
        with self.condition:
            self.queue.insert(0, (f, args, kwargs))
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
                r[0](*r[1], **r[2])
                continue

            server, request, client_address = r[1]
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
                        self._read_ready.notify_all()
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

