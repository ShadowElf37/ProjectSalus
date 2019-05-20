from server.threadpool import Poolsafe, Pool
from server.timedworker import Updater, UpdateManager
from scrape import *
from time import time, sleep

RepeaterPool = Pool(20)
RepeaterPool.launch()
Repeater = UpdateManager(RepeaterPool)

Blackbaud = BlackbaudScraper()
Blackbaud.login('ykey-cohen', 'Yoproductions3', 't')

d = Poolsafe(Blackbaud.directory)
s = Poolsafe(SageScraper().inst_menu)
RepeaterPool.pushps(d)
RepeaterPool.pushps(s)
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
    Repeater.register(ps, deltaMinutes, runinstantly=True)

    return ps


print('Scrape managers initialized.')