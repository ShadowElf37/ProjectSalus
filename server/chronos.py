import sched
import time
from .threadpool import Pool, Poolsafe
import datetime

class Chronos:
    def __init__(self, executor):
        self.push = executor
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self._chrons = {}

    def track(self, scheduler, name):
        if name in self._chrons:
            self._chrons[name].append(scheduler)
        self._chrons[name] = [scheduler]

    def get(self, name):
        return self._chrons.get(name)

    def clean(self, name):
        for c in self.get(name):
            self.terminate(c)
    def terminate(self, obj):
        self.scheduler.cancel(obj)

    def launch(self):
        self.scheduler.run()

    @staticmethod
    def repeatwrap(f, chroner, *cargs, **ckwargs):
        def wrapped(*args, **kwargs):
            # Should be a method of Chronicler to reschedule the function
            chroner(*cargs, **ckwargs)
            return f(*args, **kwargs)
        return wrapped

    def every_minutes(self, delta, ps: Poolsafe, start_at=datetime.datetime.now(), priority=0, run=False):
        if run: self.push(ps)
        pushrepeater = self.repeatwrap(self.push, self.every_minutes, delta, ps, priority=priority)

        t = start_at + datetime.timedelta(seconds=delta*60)
        return self.scheduler.enter(t.timestamp(),
                                    priority=priority, action=pushrepeater, argument=(ps,))

    def daily_at(self, _time: datetime.time, ps: Poolsafe, priority=0, run=True):
        if run: self.push(ps)
        pushrepeater = self.repeatwrap(self.push, self.daily_at, time, ps, priority=priority)

        t = datetime.datetime.combine(datetime.datetime.now().date(), _time)
        if t < time.time():
            t = datetime.datetime.combine((datetime.datetime.now()+datetime.timedelta(days=1)).date(), _time)

        return self.scheduler.enterabs(t.timestamp,
                                       priority=priority, action=pushrepeater, argument=(ps,))

    def on_date(self, datetime: datetime.datetime, ps: Poolsafe, priority=0):
        return self.scheduler.enterabs(datetime.timestamp(),
                                       priority=priority, action=self.push, argument=(ps,))

    metachrone = every_minutes
    enchrone = daily_at
    hysterochrone = on_date


if __name__ == '__main__':
    ...
