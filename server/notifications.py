import mail
from .htmlutil import *
from .chronos import Chronos
from .threadpool import ThreadManager, Promise, Minisafe
import datetime

TEMPLATES = {
    'class': 'Good {sunera} Sir.\nYour next period is {period}, which is {cls}.\nThe bell for it will ring in about 2 minutes.\n\nHave a lovely day.\n  - Salus',
    'reminder': 'Good {sunera} Sir.\nJust reminding you {class} starts in 5 minutes.\n  - Salus',
    'first-period': 'Good morning Sir.\nThe first bell will ring in about 2 minutes for {cls}.\n\nHave a lovely day.\n  - Salus',
    'mentor': 'Good morning Sir. I hope this message finds you in good health.\nThe bell is about to ring for Chavaya.\nYour Chavaya is with {mentor}.\nIt ends at {end}.\n\nHave a lovely day.\n  - Salus',
    'lunch': 'Good afternoon Sir.\nTime for some lunch.\nThe bell for your next class, {cls}, will ring at {end}.\n - Salus',
    'day-end': 'Good afternoon Sir.\nThe day is ended.\nEnjoy your afternoon!\n\n  - Salus'
}
PROVIDERS = {}
SENDER = 'ykey-cohen@emeryweiner.org'
SENDER_PASS = 'Yoproductions3'

class Notification:
    def __init__(self, template, *to, **fmt_kwargs):
        self.to = to
        self.template = template
        self.fmt_kwargs = fmt_kwargs
        self.sms = mail.MMS(SENDER, *[(recp, PROVIDERS[recp]) for recp in self.to])


    def send(self):
        conn = mail.SMTPRemote(SENDER, SENDER_PASS)
        self.sms.write(TEMPLATES[self.template].format(**Minisafe.find_minisafes_kw(self.fmt_kwargs)))
        conn.send(self.sms)
        conn.close()


def register(number, provider):
    PROVIDERS[number] = provider

def callback(f):
    return f()