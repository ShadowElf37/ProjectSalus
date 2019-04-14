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

    def push(self, httphandler):
        sorted(self.threads, key=lambda t: len(t.buffer))[0].buffer_request(httphandler)


class Maestro:
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
                server, request, client_address = self.buffer.pop(0)
            except IndexError:
                sleep(0.001)
                continue

            server.finish_request(request, client_address)
            server.shutdown_request(request)

            # httphandler(request, client_address, server)

            #req = Request(httphandler)
            #rsp = Response(httphandler)
            #handler = handlers.INDEX.get(req.path, handlers.DefaultHandler)(req, rsp)
            #handler.call()
            #handler.response.finish()