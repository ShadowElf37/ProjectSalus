from threading import *
import handlers
from time import sleep

class Overlord:
    def __init__(self, threadcount):
        self.threads = [ThreadMaestro() for i in range(threadcount)]

    def push(self, request, response):
        sorted(self.threads, key=lambda t: len(t.buffer))[0].buffer_request(request, response)

class ThreadMaestro:
    def __init__(self):
        self.buffer = []
        self.thread = Thread(target=self.mainloop, daemon=True)
        self.sleeping = True
        self.running = True

    def init_thread(self):
        self.thread.start()

    def buffer_request(self, req, rsp):
        self.buffer.append((req, rsp))

    def terminate(self):
        self.running = False

    def mainloop(self):
        while self.running:
            try:
                req, rsp = self.buffer.pop(0)
            except IndexError:
                sleep(0.001)
                continue
            handler = handlers.INDEX.get(req, handlers.DefaultHandler)(req, rsp)
            handler.call()
            handler.response.finish()