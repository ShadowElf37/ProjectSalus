import sched
import time
from .threadpool import Poolsafe
import datetime

MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY = range(0, 7)
WEEKSEC = 60*60*24*7
DAYSEC = 60*60*24

class Chronos:
    def __init__(self, executor):
        self.push = executor
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self._chrons = {}

    def track(self, scheduler, groupname):
        if groupname in self._chrons:
            self._chrons[groupname].append(scheduler)
        else:
            self._chrons[groupname] = [scheduler]

    def get(self, name):
        return self._chrons.get(name)
    def list(self):
        return self.scheduler.queue

    def clean(self, name):
        g = self.get(name)
        if not g: return
        for c in g:
            self.terminate(c)
        self._chrons[name] = []

    def terminate(self, obj):
        self.scheduler.cancel(obj)

    def start(self):
        self.scheduler.run()
    arkhomai = start

    @staticmethod
    def repeatwrap(f, chroner, *cargs, **ckwargs):
        def wrapped(*args, **kwargs):
            # Should be a method of Chronicler to reschedule the function
            chroner(*cargs, **ckwargs)
            return f(*args, **kwargs)
        return wrapped

    def delta(self, delta, ps: Poolsafe, start_at=datetime.datetime.now(), priority=0, now=False):
        if now: self.push(ps)
        pushrepeater = self.repeatwrap(self.push, self.delta, delta, ps, priority=priority)

        t = start_at + datetime.timedelta(seconds=delta*60)
        return self.scheduler.enter(t.timestamp(),
                                    priority=priority, action=pushrepeater, argument=(ps,))

    def daily(self, _time: datetime.time, ps: Poolsafe, priority=0, now=True):
        if now: self.push(ps)
        pushrepeater = self.repeatwrap(self.push, self.daily, _time, ps, priority=priority)

        t = datetime.datetime.combine(datetime.datetime.now().date(), _time).timestamp()
        if t < time.time():
            t += DAYSEC

        return self.scheduler.enterabs(t,
                                       priority=priority, action=pushrepeater, argument=(ps,))

    def every(self, daynum, ps: Poolsafe, at: datetime.time=datetime.time(0,0), priority=0, now=False):
        if now: self.push(ps)
        pushrepeater = self.repeatwrap(self.push, self.every, daynum, ps, at, priority=priority)

        now = datetime.datetime.now()
        next_day = datetime.datetime.combine((now + datetime.timedelta(days=daynum-now.weekday())).date(), at).timestamp()
        if next_day < time.time():
            next_day += WEEKSEC

        return self.scheduler.enterabs(next_day,
                                       priority=priority, action=pushrepeater, argument=(ps,))

    def annual(self, on: datetime.datetime, ps: Poolsafe, priority=0, now=False):
        if now: self.push(ps)
        pushrepeater = self.repeatwrap(self.push, self.annual, on, ps, priority=priority)

        while on < datetime.datetime.now():
            on = on.replace(year=on.year+1)

        return self.scheduler.enterabs(on.timestamp(),
                                       priority=priority, action=pushrepeater, argument=(ps,))

    def on(self, datetime: datetime.datetime, ps: Poolsafe, priority=0, now=False):
        if now: self.push(ps)

        return self.scheduler.enterabs(datetime.timestamp(),
                                       priority=priority, action=self.push, argument=(ps,))

    metakhronos = delta
    enkhronou = daily
    enkhronon = every
    horaskhronos = annual
    hysterokhronon = on


if __name__ == '__main__':
    ...
