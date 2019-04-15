from threading import *
import handlers
from time import sleep
from response import *


class Overlord:
    def __init__(self, threadcount):
        self.condition = Condition()
        self.queue = []
        self.threads = [Maestro(self.condition, self.queue) for i in range(threadcount)]

    def launch(self):
        for t in self.threads:
            t.init_thread()

    def push(self, args):
        self.pushf(None, args)

    def pushf(self, f, args):
        with self.condition:
            self.queue.insert(0, tuple([f] + list(args)))
            self.condition.notify()

class Maestro:
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
            r = None
            with self.condition:
                while True:
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
