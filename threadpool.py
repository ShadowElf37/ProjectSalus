from threading import *
import handlers
from time import sleep
from response import *


class Overlord:
    def __init__(self, threadcount):
        self.threads = [ThreadMaestro() for i in range(threadcount)]

    def launch(self):
        for t in self.threads:
            t.init_thread()

    def push(self, httphandler):
        sorted(self.threads, key=lambda t: len(t.buffer))[0].buffer_request(httphandler)


class ThreadMaestro:
    def __init__(self):
        self.buffer = []
        self.thread = Thread(target=self.mainloop, daemon=True)
        self.running = True

    def init_thread(self):
        self.thread.start()

    def buffer_request(self, httphandler):
        self.buffer.append(httphandler)

    def terminate(self):
        self.running = False

    def mainloop(self):
        while self.running:
            try:
                httphandler = self.buffer.pop(0)
            except IndexError:
                sleep(0.001)
                continue

            req = Request(httphandler)
            rsp = Response(httphandler)
            handler = handlers.INDEX.get(req, handlers.DefaultHandler)(req, rsp)
            handler.call()
            handler.response.finish()