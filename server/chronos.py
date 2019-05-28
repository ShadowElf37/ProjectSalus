from crontab import CronTab
import os.path as op
import os
import sys

t = op.abspath('test.py')
s = sys.executable
c ='"{}" "{}"'.format(s, t)
print(c)

cron = CronTab(tabfile='cron.tab')
job = cron.new(command=c)
job.minute.every(0.1)

out = job.run()
cron.write()