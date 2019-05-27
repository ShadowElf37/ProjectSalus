from server.env import EnvReader
from scrape import html

ENV = EnvReader('main.py')

SMTPSERVER = 'smtp.office365.com:587'
IMAPSERVER = 'outlook.office365.com'

USER = 'ykey-cohen@emeryweiner.org'
PASS = ENV.get('BBPASS')


# Sending mail
import smtplib

def send_mail(subject, text, *recipients, cc=(), bcc=(), sender=USER, pwd=PASS, debug=False):
    message = """From: %s
    To: %s
    Subject: %s
    Cc: %s
    Bcc: %s
    Content-Type: text/html; charset="UTF-8";

    %s""" % (sender, ', '.join(recipients), subject, ', '.join(cc), ', '.join(bcc), text)

    if debug: print('Data loaded.')
    server = smtplib.SMTP(SMTPSERVER)
    server.ehlo()
    server.starttls()
    if debug: print('SMTP initialized.')
    server.login(sender, password=pwd)
    if debug: print('Logged into server.')
    server.sendmail(sender, recipients, message)
    print('Mail sent.')
    server.quit()


# Send text messages
def send_mms(text, number, service_provider, sender='ykey-cohen@emeryweiner.org'):
    number = number.replace('-', '') + {'sprint': '@pm.sprint.com',
                                        'att': '@mms.att.net',
                                        'tmobile': '@tmomail.net',
                                        'verizon': '@vzwpix.com'}[service_provider]
    message = \
"""From: %s
To: %s

%s""" % (sender, number, text)

    server = smtplib.SMTP(SMTPSERVER)
    server.ehlo()
    server.starttls()
    server.login(USER, password=PASS)
    server.sendmail(sender, number, message)
    print('Mail sent.')
    server.quit()


# Fetching mail
import imaplib
import email


def decode_email(message):
    """ Decode email body.
    Detect character set if the header is not set.
    We try to get text/plain, but if there is not one then fallback to text/html.
    :param message_body: Raw 7-bit message body input e.g. from imaplib. Double encoded in quoted-printable and latin-1
    :return: Message body as unicode string
    """

    text = ""
    msg = message
    if msg.is_multipart():
        html = None
        for part in msg.get_payload():
            if part.get_content_charset() is None:
                # We cannot know the character set, so return decoded "something"
                text = part.get_payload(decode=True)
                continue

            charset = part.get_content_charset()

            if part.get_content_type() == 'text/plain':
                text = part.get_payload(decode=True).decode(charset)

            if part.get_content_type() == 'text/html':
                html = part.get_payload(decode=True).decode(charset)

        if text is not None:
            return text.strip()
        else:
            return html.strip()
    else:
        text = msg.get_payload(decode=True).decode(msg.get_content_charset())
        return text.strip()

def fetch_inbox(addr=USER, pwd=PASS, debug=False):
    connection = imaplib.IMAP4_SSL(IMAPSERVER)

    if debug: print('Logging in...')
    connection.login(addr, pwd)
    with connection as c:
        msgs = []
        c.select('INBOX', readonly=True)
        _, [ids] = c.search(None, 'ALL')
        for msgid in ids.split():
            _, data = c.fetch(msgid, '(RFC822)')
            for response_part in data:
                if isinstance(response_part, tuple):
                    msgs.append(email.message_from_bytes(response_part[1]))
        return msgs



SUBJECT = 'test email'
TEXT = """Good evening Mr. Rothfeder.
Your first period tomorrow is C at 8:30.
Tomorrow is a Day 3."""

if __name__ == '__main__':
    print(decode_email(fetch_inbox()[0]))
    #pm.sprint.com
    #832-258-9790@mms.att.net
    #send_mms(TEXT, '832-767-9123', 'att')