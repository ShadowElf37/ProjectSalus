from threading import *
from .config import get_config
from inspect import isfunction, ismethod, isbuiltin
import multiprocessing as mp
import queue as q

config = get_config('threads')

PCOUNT = config.get('n-procs')
TCOUNT = config.get('n-threads')
TIMEOUT = config.get('cleanup-timeout')

class Minisafe:
    def __init__(self, f, *args, **kwargs):
        self.f = f
        self.args = args
        self.kwargs = kwargs

    @staticmethod
    def find_minisafes_in(args):
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

    @staticmethod
    def test(obj):
        if isinstance(obj, Minisafe):
            return obj.call()
        return obj

    def call(self):
        return self.f(*self.args, **self.kwargs)

CALLABLE = object()
class Poolsafe:
    NONCE = object()
    def __init__(self, f, *args, **kwargs):
        if not (isfunction(f) or ismethod(f) or isbuiltin(f)): raise TypeError('Poolsafe needs a function to run.')
        self.f = f
        self.args = args
        self.kwargs = kwargs
        self.r = Poolsafe.NONCE  # None is bad because functions might actually return None and we want to see that
        self.cond = Condition(Lock())
        self.after = []

    @staticmethod
    def await_all(*pses):
        for ps in pses:
            with ps.cond:
                while ps.r is Poolsafe.NONCE:
                    ps.cond.wait()

    def wait(self):
        with self.cond:
            while self.r is Poolsafe.NONCE:
                self.cond.wait()
        return self.r

    def call(self):
        with self.cond:
            args = Minisafe.find_minisafes_in(self.args)
            kwargs = Minisafe.find_minisafes_kw(self.kwargs)
            self.r = self.f(*args, **kwargs)
            for f, args, kwargs in self.after:
                a = Minisafe.find_minisafes_in(self.args)
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


class ProcessManager:
    def __init__(self, procs=PCOUNT, threads=TCOUNT):
        self.queue = mp.Queue()
        self.procs = [Process(self.queue, threads, id=i) for i in range(procs)]

    def start(self):
        for proc in self.procs:
            proc.start()

    def alive_count_p(self):
        return len([proc for proc in self.procs if proc.alive()])
    def alive_count_t(self):
        return sum(self.report())

    def report(self):
        return [{
            'pid':proc.get_pid(),
            'num':proc.id,
            'alive':proc.alive_count()
        } for proc in self.procs]

    def join(self):
        for proc in self.procs:
            proc.join()

    def cleanup(self):
        self.queue.close()
        for proc in self.procs:
            proc.cleanup()
        self.join()

    def push(self, item):
        self.queue.put(item)
        print('Request queued.')

    def pushf(self, f, *args, **kwargs):
        self.queue.put(Poolsafe(f, *args, **kwargs))

    def push_multi(self, *ps):
        for p in ps:
            self.push(p)


class Process:
    def __init__(self, queue, threadcount=TCOUNT, id=0):
        self.proc = mp.Process(target=self._start, daemon=True, name='SalusProc%s' % id)
        self.queue = queue
        self.thread_count = threadcount
        self.id = id
        self.finished = None
        self.pool = None

    def join(self):
        self.proc.join(TIMEOUT + 1)

    def alive(self):
        return self.proc.is_alive()
    def alive_count(self):
        return self.pool.alive_count()

    def get_pid(self):
        return self.proc.pid

    def start(self):
        self.proc.start()

    def _start(self):
        self.finished = Condition()
        self.pool = ThreadManager(self.thread_count, condition=self.finished, queue=self.queue)
        self.pool.launch()
        with self.finished:
            self.finished.wait()
        return

    def cleanup(self):
        self.pool.cleanup()

class ThreadManager:
    def __init__(self, threadcount=TCOUNT, condition=Condition(), queue=q.Queue()):
        self.queue = queue
        self.threads = [RHThread(self.queue, id=i) for i in range(threadcount)]
        self.thread_count = threadcount
        self.finished = condition  # Will be used to notify a parent process that the threads have finished cleanup

    def launch(self):
        for t in self.threads:
            t.init_thread()

    def cleanup(self):
        for t in self.threads:
            t.terminate()
        for t in self.threads:
            t.thread.join(TIMEOUT-1)
        with self.finished:
            self.finished.notify_all()

    def alive_count(self):
        return len([thread for thread in self.threads if thread.alive()])

    def push(self, item):
        self.queue.put(item)

    def pushf(self, f, *args, **kwargs):
        self.queue.put(Poolsafe(f, *args, **kwargs))

    def push_multi(self, *ps):
        for p in ps:
            self.push(p)

class RHThread:
    def __init__(self, queue, id=0):
        self.queue = queue
        self.thread = Thread(target=self.mainloop, daemon=True)
        self.running = True
        self.busy = False
        self.id = id

    def init_thread(self):
        self.thread.start()
    
    def terminate(self):
        self.running = False

    def alive(self):
        return self.thread.is_alive()

    def mainloop(self):
        while self.running:
            # No timeout is needed because if this is stuck here after self.running is false, that implies that it's safe to terminate the thread anyway because it's not handling any requests
            r = self.queue.get()
            self.busy = True

            if type(r) is Poolsafe:
                r.call()
                continue

            server, stream, client_address = r
            try:
                server.finish_request(stream, client_address)
                server.shutdown_request(stream)
            except ConnectionError as e:
                server.log('An error occurred during communication with client: %s %s' % (e, e.args))
                server.CONNECTION_ERRORS += 1
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

