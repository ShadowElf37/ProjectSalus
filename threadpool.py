from threading import *
import handlers
from time import sleep
from response import *


class Overlord:
    def __init__(self, threadcount):
        self.threads = [Maestro() for i in range(threadcount)]

    def launch(self):
        for t in self.threads:
            t.init_thread()

    def push(self, args):
        sorted(self.threads, key=lambda t: len(t.buffer)+int(t.busy))[0].buffer_request(tuple([None]+list(args)))

    def pushf(self, f, args):
        sorted(self.threads, key=lambda t: len(t.buffer) + int(t.busy))[0].buffer_request(tuple([f] + list(args)))


class Maestro:
    def __init__(self):
        self.buffer = []
        self.thread = Thread(target=self.mainloop, daemon=True)
        self.running = True
        self.busy = False

    def init_thread(self):
        self.thread.start()

    def buffer_request(self, args):
        self.buffer.append(args)

    def terminate(self):
        self.running = False

    def alive(self):
        return self.thread.is_alive()

    def mainloop(self):
        while self.running:
            try:
                r = self.buffer.pop(0)
            except IndexError:
                sleep(0.001)
                continue

            self.busy = True

            if r[0] is not None:
                r[0](*r[1:])
                continue

            server, request, client_address = r[1:]
            server.finish_request(request, client_address)
            server.shutdown_request(request)
            self.busy = False
