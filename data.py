from server.persistent import AccountsSerializer
import time
import uuid
from datetime import datetime

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

@AccountsSerializer.serialized(title='', desc='', questions=[], responses={}, timestamp=0)
class Poll:
    def __init__(self, title, desc):
        self.title = title
        self.desc = desc
        self.questions = []
        self.responses = {}
        self.timestamp = time.time()
        self.id = str(uuid.uuid1())
        self.priority = 1

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

    def get_responses(self, qnum):
        return self.responses[self.questions[qnum][0]]
    def get_responses_bytext(self, qtext):
        return self.responses[qtext]

    def add_response(self, qnum, choice, user=None):
        question = self.questions[qnum][0]
        self.responses[question].append((user, choice))

    def add_question(self, qtext, *choices, freeresponse=False, number=None):
        if number is None: number = len(self.questions)
        self.questions.insert(number, (qtext, (choices if not freeresponse else None)))
        self.responses[qtext] = []

    def image_choice(self, name, imgpath):
        return (name, imgpath)

    def remove_question(self, idx):
        self.questions.pop(idx)

@AccountsSerializer.serialized(title='', text='', time=0, display_until=0, _forceon=False, _forceoff=False)
class Announcement:
    def __init__(self, title, text, display_until: int):
        self.title = title
        self.text = text
        self.timestamp = time.time()
        self._display_until = display_until
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


def create_announcement(title, text, display_until):
    a = Announcement(title, text, display_until)
    GENERAL_ANNOUNCEMENTS.append(a)
    return a
def create_poll(title, desc):
    p = Poll(title, desc)
    POLLS[p.id] = p
    return p
def create_todo(title):
    t = TodoItem(title)
    TODOLIST.append(t)
    return t
def create_event(name, desc, date, time):
    e = Event(name, desc, date, time)
    EVENTS[e.datetime] = e
    return e
def create_club(name, leader):
    c = Club(name, leader)
    CLUBS[name] = c
    leader.clubs.append(c)
    return c

def add_meeting_notes(date, *notes):
    if date not in MEETINGNOTES:
        MEETINGNOTES[date] = notes
    else:
        MEETINGNOTES[date] += notes


EVENTS = {}  # datetime:Event
CLUBS = {}  # name:Club
POLLS = {}  # id:Poll
TODOLIST = []
MEETINGNOTES = {}  # date:[str]
GENERAL_ANNOUNCEMENTS = []
try:
    AccountsSerializer.load()
    EVENTS = AccountsSerializer.get('EVENTS')
    CLUBS = AccountsSerializer.get('CLUBS')
    POLLS = AccountsSerializer.get('POLLS')
    TODOLIST = AccountsSerializer.get('TODO')
    MEETINGNOTES = AccountsSerializer.get('MEETINGNOTES')
    GENERAL_ANNOUNCEMENTS = AccountsSerializer.get('GENERAL_ANNOUNCEMENTS')
finally:
    AccountsSerializer.set('EVENTS', EVENTS)
    AccountsSerializer.set('CLUBS', CLUBS)
    AccountsSerializer.set('POLLS', POLLS)
    AccountsSerializer.set('TODO', TODOLIST)
    AccountsSerializer.set('MEETINGNOTES', MEETINGNOTES)
    AccountsSerializer.set('GENERAL_ANNOUNCEMENTS', GENERAL_ANNOUNCEMENTS)