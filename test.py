from server.notifications import *

me = '917-549-2662'
today = datetime.datetime.now()

register(me, 'sprint')

#n = Notification('class', me, period='G', cls='Calculus I Advanced', delay=5)
#Promise(n.send).call()
#exit()

pool = ThreadManager(2)
pool.launch()
c = Chronos(pool.push)

NOTIFICATIONS = {
    '8:23 am': Notification('first-period', me, period='E', cls='U.S. History'),
    '9:18 am': Notification('class', me, period='F', cls='Physics', sunera=Minisafe(sunEra)),
    '10:13 am': Notification('mentor', me, mentor='Mrs. Williams', end='11:20 am'),
    '11:23 am': Notification('class', me, period='H', cls='Judaics', sunera=Minisafe(sunEra)),
    '12:13 pm': Notification('class', me, period='A', cls='English', sunera=Minisafe(sunEra)),
    '1:10 pm': Notification('lunch', me, end='1:40', cls='Stats'),
    '1:38 pm': Notification('class', me, period='B', cls='Stats', sunera=Minisafe(sunEra)),
    '2:33 pm': Notification('class', me, period='G', cls='Calculus', sunera=Minisafe(sunEra)),
    '3:30 pm': Notification('day-end', me)
}
PROMISES = {
    t:Promise(n.send) for t,n in NOTIFICATIONS.items()
}

for t,p in PROMISES.items():
    dt = datetime.datetime.strptime(t, '%I:%M %p')
    c.on(today.replace(hour=dt.hour, minute=dt.minute, second=0), p)
c.start()
pool.cleanup()