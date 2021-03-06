import server.chronos as chronos
from scrape import *
from server.env import EnvReader
from server.threadpool import ThreadManager, Promise
from server.persistent import PersistentDict, PersistentList
from server.client import user_tokens
from server.config import get_config

HOURLY = 60
DAILY = 60*24
WEEKLY = DAILY*7
MONTHLY = DAILY*30
ANNUALLY = DAILY*365
BIANNUALLY = MONTHLY*6
QUARTERLY = MONTHLY*3

cfg = get_config('threads')
snippets = get_config('snippets')

env = EnvReader('main.py')
USER = env['BBUSER']
PASS = env['BBPASS']

print('Initializing Chronomancer...')
updater_pool = ThreadManager(cfg.get('n-scrapes'))
updater_pool.launch()
chronomancer = chronos.Chronos(updater_pool.push)
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
        global DIRECTORY, DIRECTORY_HTML
        v = updater(*args, **kwargs)
        update_email_map(v)
        # Sort it since it pops out in sorted chunks but isn't sorted globally
        v = [(k,v[k]) for k in sorted(v.keys(), key=lambda k: k[k.find(' ')+1:])]
        DIRECTORY_HTML = update_directory_html(v)
        return DIRECTORY.points(dict(v))
    return u
def update_teachers(updater):
    def u(*args, **kwargs):
        global TEACHERS, TEACHER_HTML
        v = updater(*args, **kwargs)
        update_email_map(v)
        # Sort it because I want to
        v = [(k, v[k]) for k in sorted(v.keys(), key=lambda k: k[k.find(' ') + 1:])]
        TEACHER_HTML = update_teacher_html(v)
        return TEACHERS.points(dict(v))
    return u
def update_menu(updater):
    def u(*args, **kwargs):
        global SAGEMENU, SAGEMENUINFO
        u = updater(*args, **kwargs)
        return SAGEMENU.points(u[0]), SAGEMENUINFO.points(u[1])
    return u
def update_sports(updater):
    def u(*args, **kwargs):
        global SPORTCAL
        return SPORTCAL.points(updater(*args, **kwargs))
    return u

def update_directory_html(s_list):
    html = [snippets.get('dir-entry').format(
        phones = '\n'.join([snippets.get('dir-phone').format(
                phone_number = entry[t],
                phone_type = t.title()
            ) for t in ['home', 'cell'] if entry.get(t)]) or snippets.get('no-dir-phone'),
        fname = name[:name.find(' ')],
        lname = name[name.find(' ')+1:],
        email = get(entry, 'email', 'No email on record.'),
        addr = get(entry, 'address', 'No address on record.'),
        city = get(entry, 'city', 'No city'),
        state = get(entry, 'state', 'no state.'),
        zip = get(entry, 'zip', '').split('-')[0],
        reg = 'Not registered' if user_tokens.find(lambda a: a.name == name) is None else 'Registered',
        bbid = entry['id'],
        grad = entry['year'],
        grade = entry['grade']
    ) for name, entry in s_list]
    return '\n'.join(html)
def update_teacher_html(t_list):
    html = [snippets.get('tdir-entry').format(
            fname = name[:name.find(' ')],
            lname = name[name.find(' ') + 1:],
            phone = get(entry, 'phone', snippets.get('no-dir-phone')),
            bbid = entry['id'],
            dept = ', '.join(entry['dept']) or 'Dept. of Mysterious Persons',
            email = entry['email'],
            reg = 'Not registered' if user_tokens.find(lambda a: a.name == name) is None else 'Registered',
        ) for name, entry in t_list]
    return '\n'.join(html)

def update_email_map(d):
    global DIR_EMAIL_MAP
    for name in d:
        email = get(d[name], 'email', None)
        if email is not None:
            DIR_EMAIL_MAP[name] = email

def dsetter(dict, key, updaterf):
    def u(*args, **kwargs):
        if type(updaterf) is Minisafe:
            v = updaterf.call()
        elif type(updaterf) is Promise:
            v = updaterf.call()
        else:
            v = updaterf(*args, **kwargs)
        dict[key] = v
        return v
    return u

DIRECTORY = PersistentDict()
TEACHERS = PersistentDict()
SAGEMENU = PersistentDict()
SAGEMENUINFO = PersistentDict()
SPORTCAL = PersistentList()
DIR_EMAIL_MAP = {}

d = Promise(update_directory(bb_login_safe(Blackbaud.directory, USER, PASS)))
t = Promise(update_teachers(bb_login_safe(Blackbaud.teacher_directory, USER, PASS)))
sp = Promise(update_sports(bb_login_safe(Blackbaud.sports_calendar, USER, PASS)), end_date=firstlast_of_month(+1)[1])
s = Promise(update_menu(Sage.inst_menu))

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
    CLASSES = PersistentDict()
    CLASS_TOPICS = PersistentDict()
    PROFILE_DETAILS = PersistentDict()
    DIRECTORY = PersistentDict(d.wait())
    Promise.await_all(d, t, s, sp)

CLASS_UPDATERS = {}
TOPICS_UPDATERS = {}


v = [(k, DIRECTORY[k]) for k in sorted(DIRECTORY.keys(), key=lambda k: k[k.find(' ') + 1:])]
DIRECTORY_HTML = update_directory_html(v)
v = [(k, TEACHERS[k]) for k in sorted(TEACHERS.keys(), key=lambda k: k[k.find(' ') + 1:])]
TEACHER_HTML = update_teacher_html(v)

update_email_map(DIRECTORY)
update_email_map(TEACHERS)

DataSerializer.set('TOPICS', CLASS_TOPICS)
DataSerializer.set('DIRECTORY', DIRECTORY)
DataSerializer.set('TEACHERS', TEACHERS)
DataSerializer.set('SAGEMENU', SAGEMENU)
DataSerializer.set('SAGEMENUINFO', SAGEMENUINFO)
DataSerializer.set('CLASSES', CLASSES)
DataSerializer.set('PROFILES', PROFILE_DETAILS)
DataSerializer.set('SPORTCAL', SPORTCAL)