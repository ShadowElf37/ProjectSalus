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


EVENTS = {}
CLUBS = {}
try:
    MiscSerializer.load()
    EVENTS = MiscSerializer.get('EVENTS')
    CLUBS = MiscSerializer.get('CLUBS')
except (JSONDecodeError, KeyError):
    pass
MiscSerializer.set('EVENTS', EVENTS)
MiscSerializer.set('CLUBS', CLUBS)
