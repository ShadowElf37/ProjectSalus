import heapq
from time           import time
from threading      import Lock, Condition

class Update:
    def __init__(self, minutes, data, name=None):
        # Scrape every once in a while
        self.delta = minutes * 60
        self.data = data
        self.name = name
        self.next = time() + self.delta
        self.update()

    def update(self):
        self.next = time() + self.delta

    def __le__(self, other):
        return self.next <= other.next
    def __lt__(self, other):
        return self.next < other.next

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
                        if nextjob.next <= time():
                            nextjob.update()
                            heapq.heapreplace(self.updates, nextjob)
                            break
                        else:
                            self.cond.wait(time() - nextjob.next)
                    else: self.cond.wait()
            self.output(nextjob)

    def stop(self):
        self.running = False
        with self.cond:
            self.cond.notify_all()

    def register(self, data, minutes=60, now=False, name=None):
        self.register_update(Update(minutes, data, name), now)

    def register_update(self, update: Update, now=False):
        with self.cond:
            heapq.heappush(self.updates, update)
            self.cond.notify_all()
        if now:
            self.output(update)

    def find_update(self, name):
        return next(filter(lambda u: u.name == name, self.updates), None)
