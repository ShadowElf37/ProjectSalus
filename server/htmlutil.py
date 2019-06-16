from html import escape, unescape
import re
import datetime
from .config import get_config

snippets = get_config('snippets')
def snippet(key, *fmtarg, **fmtkw):
    return snippets.get(key).format(*fmtarg, **fmtkw)

def css(s):
    return '<link rel="stylesheet" href="{}">'.format(s)

def js(s):
    return '<script type="text/javascript" src="{}"></script>'.format(s)

def getTime():
    return datetime.datetime.now().strftime('%I:%M')
def getAmPm():
    return datetime.datetime.now().strftime('%p')
def getDate():
    return datetime.datetime.now().strftime('%m/%d/%Y')
WEEKDAYNAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
ISOWEEKDAYNAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

def ordinal(n: int):
    return str(n) + {'1':'st', '2':'nd', '3':'rd'}.get(str(n)[-1], 'th')

def now():
    return datetime.datetime.now()

def sunEra():
    n = now()
    return 'morning' if n.hour < 12 else 'afternoon' if n.hour < 17 else 'evening'

def sp(n=1):
    return '&nbsp;'*n