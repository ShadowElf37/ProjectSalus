import server.chronos as chronos
from scrape import *
from server.env import EnvReader

HOURLY = 60
DAILY = 60*24
WEEKLY = DAILY*7
MONTHLY = DAILY*30
ANNUALLY = DAILY*365
BIANNUALLY = MONTHLY*6
QUARTERLY = MONTHLY*3

env = EnvReader('main.py')

updater_pool = Pool(20)
updater_pool.launch()
chronomancer = chronos.Chronos(updater_pool.pushps)
updater_pool.pushf(chronomancer.arkhomai)

Blackbaud = BlackbaudScraper()
Blackbaud.login(env['BBUSER'], env['BBPASS'], 't')

d = Poolsafe(Blackbaud.directory)
s = Poolsafe(SageScraper().inst_menu)

chronomancer.horaskhronos(datetime.datetime.strptime('8/15/2019', '%m/%d/%Y'), d, now=True)
chronomancer.horaskhronos(datetime.datetime.strptime('1/1/2020', '%m/%d/%Y'), d)
chronomancer.enkhronon(chronos.SUNDAY, s, now=True)
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
    d = chronomancer.metakhronos(deltaMinutes, ps, now=True)
    chronomancer.track(d, account.name)

    return ps


print('Scrape managers initialized.')
