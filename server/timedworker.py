from time import sleep, time
from server.threadpool import Poolsafe

class UpdateManager:
    def __init__(self, pool):
        self.pool = pool
        self.updates = []

    def launch(self):
        self.pool.pushf(self.mainloop)

    def mainloop(self):
        while True:
            self.check()
            sleep(1)

    def check(self):
        for updater in self.updates:
            ps = updater.poll()
            if ps:
                self.pool.pushps(ps)

    def register(self, psf: Poolsafe, deltaMinutes=30, runinstantly=False):
        u = Updater(self, deltaMinutes, psf)
        self.updates.append(u)
        if runinstantly:
            self.pool.pushps(u.f)
        return u


class Updater:
    def __init__(self, manager, deltaMinutes, psf: Poolsafe):
        # Scrape every once in a while
        self.start = time()
        self.delta = deltaMinutes * 60
        self.updatetime = self.start + self.delta
        self.f = psf
        self.manager = manager

    def poll(self):
        if self.updatetime <= time():
            self.updatetime = time() + self.delta
            return self.f
        return None
