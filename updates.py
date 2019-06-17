import server.chronos as chronos
from scrape import *
from server.env import EnvReader
from server.threadpool import Pool, Poolsafe
from server.persistent import PersistentDict

HOURLY = 60
DAILY = 60*24
WEEKLY = DAILY*7
MONTHLY = DAILY*30
ANNUALLY = DAILY*365
BIANNUALLY = MONTHLY*6
QUARTERLY = MONTHLY*3

env = EnvReader('main.py')
USER = env['BBUSER']
PASS = env['BBPASS']

print('Initializing Chronomancer...')
updater_pool = Pool(32)
updater_pool.launch()
chronomancer = chronos.Chronos(updater_pool.pushps)
updater_pool.pushf(chronomancer.arkhomai)

Blackbaud = BlackbaudScraper()
Blackbaud.login(USER, PASS)
Sage = SageScraper()

def bb_login_safe(f, user, pwd):
    def safe(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except StatusError as e:
            try:
                f.__self__.login(user, pwd)
            except StatusError:
                return
            return f(*args, **kwargs)
    return safe

def update_directory(updater):
    def u(*args, **kwargs):
        global DIRECTORY
        DIRECTORY.point(updater(*args, **kwargs))
        return DIRECTORY
    return u
def update_teachers(updater):
    def u(*args, **kwargs):
        global TEACHERS
        TEACHERS.point(updater(*args, **kwargs))
        return TEACHERS
    return u
def update_menu(updater):
    def u(*args, **kwargs):
        global SAGEMENU, SAGEMENUINFO
        u = updater(*args, **kwargs)
        SAGEMENU.point(u[0])
        SAGEMENUINFO.point(u[1])
        return SAGEMENU, SAGEMENUINFO
    return u
def update_sports(updater):
    def u(*args, **kwargs):
        global SPORTCAL
        SPORTCAL.point(updater(*args, **kwargs))
        return SPORTCAL
    return u

def dsetter(dict, key, updaterf):
    def u(*args, **kwargs):
        v = updaterf(*args, **kwargs)
        dict[key] = v
        return v
    return u

d = Poolsafe(update_directory(bb_login_safe(Blackbaud.directory, USER, PASS)))
t = Poolsafe(update_teachers(bb_login_safe(Blackbaud.teacher_directory, USER, PASS)))
sp = Poolsafe(update_sports(bb_login_safe(Blackbaud.sports_calendar, USER, PASS)), end_date=firstlast_of_month(+1)[1])
s = Poolsafe(update_menu(Sage.inst_menu))

chronomancer.horaskhronos(datetime.datetime.strptime('8/15/2019', '%m/%d/%Y'), d, now=True)
chronomancer.horaskhronos(datetime.datetime.strptime('1/1/2020', '%m/%d/%Y'), d)
chronomancer.horaskhronos(datetime.datetime.strptime('8/15/2019', '%m/%d/%Y'), t, now=True)
chronomancer.horaskhronos(datetime.datetime.strptime('1/1/2020', '%m/%d/%Y'), t)
chronomancer.daily(datetime.time(15, 0), sp, now=True)
chronomancer.enkhronon(chronos.SUNDAY, s, now=True)

from server.persistent import Manager
from json import JSONDecodeError
DataSerializer = Manager.make_serializer('scrapes.json')
try:
    # Yes, these will be overwritten by the updaters as they run and set, but we're not mandatorily blocking in this paradigm, so we still get the performance boost AND fresh data
    DataSerializer.load()
    DIRECTORY = DataSerializer.get('DIRECTORY')
    TEACHERS = DataSerializer.get('TEACHERS')
    SAGEMENU = DataSerializer.get('SAGEMENU')
    SAGEMENUINFO = DataSerializer.get('SAGEMENUINFO')
    CLASSES = DataSerializer.get('CLASSES')
    CLASS_TOPICS = DataSerializer.get('TOPICS')
    PROFILE_DETAILS = DataSerializer.get('PROFILES')
    SPORTCAL = DataSerializer.get('SPORTCAL')
    print('Using cached scrape data.')
except (JSONDecodeError, KeyError):
    # updater_pool.pushps_multi(d, t, s)
    DIRECTORY = PersistentDict(d.wait())
    TEACHERS = PersistentDict(t.wait())
    s = s.wait()
    SAGEMENU, SAGEMENUINFO = PersistentDict(s[0]), PersistentDict(s[1])
    SPORTCAL = PersistentDict(sp.wait())
    CLASSES = PersistentDict()
    CLASS_TOPICS = PersistentDict()
    PROFILE_DETAILS = PersistentDict()

CLASS_UPDATERS = {}
TOPICS_UPDATERS = {}

DataSerializer.set('TOPICS', CLASS_TOPICS)
DataSerializer.set('DIRECTORY', DIRECTORY)
DataSerializer.set('TEACHERS', TEACHERS)
DataSerializer.set('SAGEMENU', SAGEMENU)
DataSerializer.set('SAGEMENUINFO', SAGEMENUINFO)
DataSerializer.set('CLASSES', CLASSES)
DataSerializer.set('PROFILES', PROFILE_DETAILS)
DataSerializer.set('SPORTCAL', SPORTCAL)

from server.threadpool import CALLABLE

# DEPRECATED - use Poolsafe(bb_login_safe(f, user, pass)) and chronomancer.f(ps)
def register_bb_updater(account, cachekey, f, args, deltaMinutes, **kwargs):
    def update(f, *args, **kwargs):
        session = BlackbaudScraper()
        session.cookies['t'] = account.bb_t
        if not account.bb_t:
            try:
                c = session.login(*account.bb_auth)
            except StatusError:
                return
            # print(c, account.bb_auth)
            account.bb_t = c['t']

        newargs = []
        for arg in args:
            if type(arg) is tuple and arg[0] is CALLABLE:
                newargs.append(arg[1]())
            else:
                newargs.append(arg)

        try:
            r = f(session, *newargs, **kwargs)
        except StatusError:
            try:
                c = session.login(*account.bb_auth)
            except StatusError:
                return
            account.bb_t = c['t']
            try:
                r = f(session, *newargs, **kwargs)
            except StatusError:
                return
        except Exception as e:
            print(f, args, kwargs)
            raise e
        account.bb_cache[cachekey] = r
        return r

    ps = Poolsafe(update, f, *args, **kwargs)
    d = chronomancer.metakhronos(deltaMinutes, ps, now=True)
    chronomancer.track(d, account.name)

    return ps
