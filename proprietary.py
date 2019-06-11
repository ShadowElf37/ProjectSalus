from server.persistent import Manager
from json import JSONDecodeError

MiscSerializer = Manager.make_serializer('miscdata.json')


@MiscSerializer.serialized(name='', leader=None, members=[], announcements=[], meeting_dates=[])
class Club:
    def __init__(self, name, leader_account):
        self.name = name
        self.leader = leader_account
        self.members = []
        self.announcements = []
        self.meeting_dates = []

@MiscSerializer.serialized(name='', desc='', date='', time='')
class Event:
    def __init__(self, name, description, date, time):
        self.name = name
        self.desc = description
        self.date = date
        self.time = time

@MiscSerializer.serialized()
class TodoItem:
    STATES = [
        'Pending Approval',
        'Approved',
        'Assigned to Representative',
        'Complete',
    ]
    def __init__(self, title):
        self.title = title
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


@MiscSerializer.serialized()
class Poll:
    def __init__(self, title, desc):
        self.title = title
        self.desc = desc
        self.questions = []
        self.responses = {}

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

    def remove_question(self, idx):
        self.questions.pop(idx)

EVENTS = {}  # date:Event
CLUBS = {}  # name:Club
POLLS = {}  # name:Poll
TODOLIST = []
try:
    MiscSerializer.load()
    EVENTS = MiscSerializer.get('EVENTS')
    CLUBS = MiscSerializer.get('CLUBS')
    POLLS = MiscSerializer.get('POLLS')
    TODOLIST = MiscSerializer.get('TODO')
finally:
    MiscSerializer.set('EVENTS', EVENTS)
    MiscSerializer.set('CLUBS', CLUBS)
    MiscSerializer.set('POLLS', POLLS)
    MiscSerializer.set('TODO', TODOLIST)