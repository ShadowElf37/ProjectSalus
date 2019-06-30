from server.persistent import *
from datetime import datetime
from json import JSONDecodeError
from scrape import week_of
import time
import uuid

@AccountsSerializer.serialized(name='', leader=None, members=[], announcements=[], meeting_dates=[], admin_access=[])
class Club:
    def __init__(self, name, leader_account):
        self.name = name
        self.leader = leader_account
        self.members = []
        self.announcements = []
        self.meeting_datetimes = []
        self.admin_access = []

@AccountsSerializer.serialized(name='', desc='', date='', time='', datetime=None)
class Event:
    def __init__(self, name, description, date, time):
        self.name = name
        self.desc = description
        self.date = date
        self.time = time
        self.datetime = self._gen_dt()

    def _gen_dt(self):
        return datetime.combine(datetime.strptime(self.date, '%m/%d/%Y').date(),
                                         datetime.strptime(self.time, '%I:%M %p').time())

    def reschedule(self, date, time):
        self.date = date
        self.time = time
        self.datetime = self._gen_dt()

@AccountsSerializer.serialized(title='', state=0, complete=False, assigned=None)
class TodoItem:
    STATES = [
        'Pending Approval',
        'Approved',
        'Assigned to Representative',
        'Complete',
    ]
    def __init__(self, title):
        self.title = title
        self.details = ''
        self.state = 0
        self.complete = False
        self.assigned = None

    def assign_to(self, acnt):
        self.assigned = acnt
    def finish(self):
        self.complete = True
    def advance(self):
        self.state += 1
    def get_state(self):
        return TodoItem.STATES[self.state]

@AccountsSerializer.serialized(title='', questions=[], responses={}, timestamp=0, priority=1, id='', reusable=True)
class Poll:
    FREERESPONSE = '#free'
    SCALE = '#scale'
    MULTIPLECHOICE = '#multi'

    def __init__(self, title, reusable=False):
        self.title = title
        self.questions = []
        self.responses = {}
        self.timestamp = time.time()
        self.id = str(uuid.uuid1())
        self.priority = 1
        self.reusable = reusable

    def __lt__(self, o):
        return self.priority < o.priority
    def __le__(self, o):
        return self.priority <= o.priority
    def __gt__(self, o):
        return self.priority > o.priority
    def __ge__(self, o):
        return self.priority >= o.priority
    def __eq__(self, o):
        return self.priority == o.priority
    def __ne__(self, o):
        return self.priority != o.priority

    @staticmethod
    def image_choice(name, imgpath):
        return name, imgpath

    def get_responses(self, qnum):
        return self.responses[self.questions[qnum][0]]
    def get_responses_bytext(self, qtext):
        return self.responses[qtext]
    def user_has_responded(self, user):
        for r in self.responses.values():
            if user in r:
                return True
        return False

    def add_response(self, qnum, choice, user=None):
        question = self.questions[qnum][0]
        self.responses[question].append((user, choice))

    def add_question(self, qtext, *choices, _type=MULTIPLECHOICE, qnumber=None):
        self.questions.insert(qnumber or len(self.questions), (qtext, (choices if _type == self.MULTIPLECHOICE else _type)))
        self.responses[qtext] = []

    def remove_question(self, idx):
        del self.questions[idx]

@AccountsSerializer.serialized(title='', text='', timestamp=0, _display_until=0, _forceon=False, _forceoff=False)
class Announcement:
    def __init__(self, title, text, displayuntil: int):
        self.title = title
        self.text = text
        self.timestamp = time.time()
        self._display_until = displayuntil
        self._forceon = False
        self._forceoff = False

    @property
    def displayed(self):
        return self._forceon or time.time() < self._display_until and not self._forceoff

    def display_until(self, time: int):
        self._display_until = time

    def force_off(self):
        self._forceoff = True
        self._forceon = False
    def force_on(self):
        self._forceon = True
        self._forceoff = False
    def force_none(self):
        self._forceon = False
        self._forceoff = False

@AccountsSerializer.serialized(days=[None]*5, week=[])
class MaamadWeek:
    def __init__(self, weekofdt):
        self.days = [('', '')]*5
        self.week = list(map(lambda d: d.strftime('%m/%d/%Y'), week_of(weekofdt)))[1:-1]

    def set_day(self, n, activity, desc):
        self.days[n] = (activity, desc)

    def get_date(self, dstr):
        return self.days[self.week.index(dstr)]
    def get_daynum(self, n):
        return self.days[n]
    def is_this_week(self, manual=None):
        return (manual if manual else datetime.now().strftime('%m/%d/%Y')) in self.week


def create_announcement(title, text, display_until: int):
    global GENERAL_ANNOUNCEMENTS
    a = Announcement(title, text, display_until)
    GENERAL_ANNOUNCEMENTS.append(a)
    return a
def create_poll(title):
    global POLLS
    p = Poll(title)
    POLLS[p.id] = p
    return p
def create_todo(title):
    global TODOLIST
    t = TodoItem(title)
    TODOLIST.append(t)
    return t
def create_event(name, desc, date, time):
    global EVENTS
    e = Event(name, desc, date, time)
    EVENTS[e.datetime] = e
    return e
def create_club(name, leader):
    global CLUBS
    c = Club(name, leader)
    CLUBS[name] = c
    leader.clubs.append(c)
    return c
def create_maamad_week(weekofdstr):
    global MAAMADS
    m = MaamadWeek(datetime.strptime(weekofdstr, '%m/%d/%Y'))
    MAAMADS.append(m)
    return m

def add_meeting_notes(date, *notes):
    global MEETINGNOTES
    if date not in MEETINGNOTES:
        MEETINGNOTES[date] = notes
    else:
        MEETINGNOTES[date] += notes


try:
    AccountsSerializer.load()
    EVENTS = AccountsSerializer.get('EVENTS')
    CLUBS = AccountsSerializer.get('CLUBS')
    POLLS = AccountsSerializer.get('POLLS')
    TODOLIST = AccountsSerializer.get('TODO')
    MEETINGNOTES = AccountsSerializer.get('MEETINGNOTES')
    GENERAL_ANNOUNCEMENTS = AccountsSerializer.get('GENERAL_ANNOUNCEMENTS')
    MAAMADS = AccountsSerializer.get('MAAMADS')
except (KeyError, JSONDecodeError):
    EVENTS = PersistentDict()
    CLUBS = PersistentDict()  # name:Club
    POLLS = PersistentDict()  # id:Poll
    TODOLIST = PersistentList()
    MEETINGNOTES = PersistentDict()
    GENERAL_ANNOUNCEMENTS = PersistentList()
    MAAMADS = PersistentList()

AccountsSerializer.set('EVENTS', EVENTS)
AccountsSerializer.set('CLUBS', CLUBS)
AccountsSerializer.set('POLLS', POLLS)
AccountsSerializer.set('TODO', TODOLIST)
AccountsSerializer.set('MEETINGNOTES', MEETINGNOTES)
AccountsSerializer.set('GENERAL_ANNOUNCEMENTS', GENERAL_ANNOUNCEMENTS)
AccountsSerializer.set('MAAMADS', MAAMADS)
