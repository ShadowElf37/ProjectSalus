import sched
import time
from .threadpool import Pool, Poolsafe
import datetime

class Chronicle:
    def __init__(self, name=None):
        ...

class Chronicler:
    def __init__(self, pool: Pool):
        self.pool = pool
        self.push = self.pool.pushps
        self.scheduler = sched.scheduler(time.time, time.sleep)

    @staticmethod
    def repeatwrap(f, chroner, *cargs, **ckwargs):
        def wrapped(*args, **kwargs):
            # Should be a method of Chronicler to reschedule the function
            chroner(*cargs, **ckwargs)
            return f(*args, **kwargs)
        return wrapped


    def every_minutes(self, delta, ps: Poolsafe, priority=0):
        pushrepeater = self.repeatwrap(self.push, self.every_minutes, delta, ps, priority=priority)
        return self.scheduler.enter(delta*60,
                                    priority=priority, action=pushrepeater, argument=(ps,))

    def daily_at(self, time: datetime.time, ps: Poolsafe, priority=0):
        pushrepeater = self.repeatwrap(self.push, self.daily_at, time, ps, priority=priority)
        return self.scheduler.enterabs(datetime.datetime.combine(datetime.datetime.now().date(), time).timestamp(),
                                       priority=priority, action=pushrepeater, argument=(ps,))

    def on_date(self, datetime: datetime.datetime, ps: Poolsafe, priority=0):
        return self.scheduler.enterabs(datetime.timestamp(),
                                       priority=priority, action=self.push, argument=(ps,))

if __name__ == '__main__':
    ...