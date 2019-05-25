from server.threadpool import Poolsafe, Pool
from server.timedworker import UpdateManager
from scrape import *
from time import time, sleep
from server.env import EnvReader

env = EnvReader('main.py')

repeater_pool = Pool(20)
repeater_pool.launch()
repeater = UpdateManager(repeater_pool.pushf)
repeater_pool.pushf(repeater.start)

Blackbaud = BlackbaudScraper()
Blackbaud.login(env['BBUSER'], env['BBPASS'], 't')

d = Poolsafe(Blackbaud.directory)
s = Poolsafe(SageScraper().inst_menu)
repeater_pool.pushps(d)
repeater.register(s, 60*24*7, now=True)
DIRECTORY = d.wait()
SAGEMENU, SAGEMENUINFO = s.wait()

FUNC = ...


def register_bb_updater(account, cachekey, f, args, deltaMinutes, **kwargs):
    def update(f, *args, **kwargs):
        session = BlackbaudScraper()
        session.default_cookies['t'] = account.bb_t
        if not account.bb_t:
            c = session.login(*account.bb_auth, 't')
            print(c, account.bb_auth)
            account.bb_t = c['t']

        newargs = []
        for arg in args:
            if type(arg) is tuple and arg[0] is FUNC:
                newargs.append(arg[1]())
            else:
                newargs.append(arg)

        try:
            r = f(session, *newargs, **kwargs)
        except Exception as e:
            print(f, args, kwargs)
            raise e
        account.bb_cache[cachekey] = r
        return r

    ps = Poolsafe(update, f, *args, **kwargs)
    repeater.register(ps, deltaMinutes, now=True)

    return ps


print('Scrape managers initialized.')
