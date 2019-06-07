from html import escape, unescape
import re
import datetime


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