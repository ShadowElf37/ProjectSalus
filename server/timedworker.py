import heapq
from time           import time
from threading      import Lock, Condition

class Update:
    def __init__(self, minutes, data):
        # Scrape every once in a while
        self.delta = minutes * 60
        self.data = data
        self.update()

    def update(self):
        self.next = time() + self.delta

    def __le__(self, other):
        return self.next <= other.next

class UpdateManager:
    def __init__(self, cb):
        self.cond = Condition(Lock())
        self.output = lambda update: cb(update.data)
        self.updates = []
        self.running = False

    def start(self):
        with self.cond:
            if self.running:
                raise ValueError("UpdateMan already running")
            self.running = True
        while self.running:
            with self.cond:
                while True:
                    if not self.running: return
                    if self.updates:
                        nextjob = self.updates[0]
                        now = time()
                        if nextjob.next <= now:
                            nextjob.update()
                            heapq.heapreplace(self.updates, nextjob)
                            break
                        else:
                            self.cond.wait(now - nextjob.next)
                    else: self.cond.wait()
            self.output(nextjob)

    def stop(self):
        self.running = False
        with self.cond:
            self.cond.notify_all()

    def register(self, data, minutes=30, now=False):
        update = Update(minutes, data)
        with self.cond:
            heapq.heappush(self.updates, update)
            self.cond.notify_all()
        if now:
            self.output(update)
