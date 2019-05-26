from server.config import get_config

pwds = get_config('passwords')

SERVER = 'smtp.office365.com:587'

SUBJECT = 'test email'
TEXT = """Good evening Mr. Rothfeder.
Your first period tomorrow is C at 8:30.
Tomorrow is a Day 3."""

pwd = 'Yoproductions3'

# Send the mail
import smtplib

def send_mail(subject, text, *recipients, cc=(), bcc=(), sender='ykey-cohen@emeryweiner.org', debug=False):
    message = """From: %s
    To: %s
    Subject: %s
    Cc: %s
    Bcc: %s
    Content-Type: text/html; charset="UTF-8";

    %s""" % (sender, ', '.join(recipients), subject, ', '.join(cc), ', '.join(bcc), text)

    if debug: print('Data loaded.')
    server = smtplib.SMTP(SERVER)
    server.ehlo()
    server.starttls()
    if debug: print('SMTP initialized.')
    server.login("ykey-cohen@emeryweiner.org", password=pwd)
    if debug: print('Logged into server.')
    server.sendmail(sender, recipients, message)
    print('Mail sent.')
    server.quit()


def send_mms(text, number, domain, sender='ykey-cohen@emeryweiner.org'):
    number = number.replace('-', '') + {'sprint': '@pm.sprint.com',
                                        'att': '@mms.att.net',
                                        'tmobile': '@tmomail.net',
                                        'verizon': '@vzwpix.com'}[domain]
    message = \
"""From: %s
To: %s

%s""" % (sender, number, text)

    server = smtplib.SMTP(SERVER)
    server.ehlo()
    server.starttls()
    server.login("ykey-cohen@emeryweiner.org", password=pwd)
    server.sendmail(sender, number, message)
    print('Mail sent.')
    server.quit()

if __name__ == '__main__':
    #pm.sprint.com
    #832-258-9790@mms.att.net
    send_mms(TEXT, '832-767-9123', 'att')
