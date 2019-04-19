from config import get_config

pwds = get_config('passwords')

SERVER = 'smtp.office365.com:587'

SUBJECT = 'test email'
TEXT = """<p class="MsoNormal" style="color: purple;">testing 123</p>"""

# Send the mail
import smtplib

def send_mail(subject, text, *recipients, cc=[], bcc=[], sender='ykey-cohen@emeryweiner.org', debug=False):
    message = """From: %s
    To: %s
    Subject: %s
    Cc: %s
    Bcc: %s
    Content-Type: text/html; charset="ISO-8859-1";

    %s
    """ % (sender, ', '.join(recipients), subject, ', '.join(cc), ', '.join(bcc), text)

    if debug: print('Data loaded.')
    server = smtplib.SMTP(SERVER)
    server.ehlo()
    server.starttls()
    if debug: print('SMTP initialized.')
    server.login("ykey-cohen@emeryweiner.org", password=pwds.get('0'))
    if debug: print('Logged into server.')
    server.sendmail(sender, recipients, message)
    print('Mail sent.')
    server.quit()

if __name__ == '__main__':
    send_mail(SUBJECT, TEXT, 'mgoldstein@emeryweiner.org')