from server.env import EnvReader
from scrape import html, soup_without
from bs4 import BeautifulSoup
import datetime

ENV = EnvReader('main.py')

SMTPHOST = 'smtp.office365.com:587'
IMAPHOST = 'outlook.office365.com'

USER = 'ykey-cohen@emeryweiner.org'
PASS = ENV.get('BBPASS')

# Sending mail
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

class Remote:
    def __init__(self, user=USER, pwd=PASS, remote=SMTPHOST):
        self.remote = remote
        self.open()
        self.user = user
        self.pwd = pwd
        self.login()

    def open(self):
        self.server = smtplib.SMTP(self.remote)
        self.server.ehlo()
        self.server.starttls()

    def login(self):
        self.server.login(self.user, password=self.pwd)

    def close(self):
        self.server.quit()

    def send(self, message):
        self.server.sendmail(message.sender, message.recipients, message.compile())

class Message:
    def __init__(self, sender, *recp):
        self.sender = sender
        self.recipients = recp
        self.mime = MIMEMultipart('mixed')
        self.body = MIMEMultipart('alternative')
        self.mime.attach(self.body)

    def write(self, data):
        m = MIMEText(data)
        self.body.attach(m)
        return m

    def attach(self, filepath):
        f = MIMEApplication(open(filepath, 'rb').read())
        f.add_header('Content-Disposition', 'attachment', filename=os.path.split(filepath)[-1])
        self.mime.attach(f)
        return f


class Email(Message):
    def __init__(self, *recipients, subject='', sender=USER, cc=(), bcc=()):
        super().__init__(sender, *recipients)
        self.subject = subject
        self.cc = cc
        self.bcc = bcc
        self.content_type = 'text/html'

    def set_subject(self, string):
        self.subject = string

    def compile(self):
        self.mime['From'] = self.sender
        self.mime['To'] = ', '.join(self.recipients)
        self.mime['Subject'] = self.subject
        self.mime['Cc'] = ', '.join(self.cc)
        self.mime['Bcc'] = ', '.join(self.bcc)
        return self.mime.as_string()

class MMS(Message):
    PROVIDERS = {'sprint': '@pm.sprint.com',
                'att': '@mms.att.net',
                'tmobile': '@tmomail.net',
                'verizon': '@vzwpix.com'}

    def __init__(self, *recipients, sender=USER):
        """Give recipients as tuples with (number, service provider)"""
        if type(recipients[0]) not in (tuple, list):
            raise TypeError('Recipients for MMS must be (number, provider) tuples')
        self.recipients = [r[0].replace('-', '')+MMS.PROVIDERS[r[1]] for r in recipients]
        super().__init__(sender, *self.recipients)

    def compile(self):
        self.mime['From'] = self.sender
        self.mime['To'] = ', '.join(self.recipients)
        return self.mime.as_string()


# Fetching mail
import imaplib
import email
import codecs
import os

class IMAPAttachment:
    def __init__(self, name):
        self.name = name
        self.path = os.getcwd()
        self.contents = []

    def __repr__(self):
        return 'Attachment "{}" with contents of len {}'.format(self.name, sum(map(len, self.contents)))
    __str__ = __repr__

    def dump(self, path=None):
        if path: self.set_path(path)
        with open(self.path, 'wb') as f:
            f.write(self.read())

    def read(self):
        return b''.join(self.contents)

    def set_path(self, path):
        if os.path.isdir(path):
            path = os.path.join(path, self.name)
        self.path = path

    def write(self, data):
        if type(data) is not bytes:
            raise TypeError('Attachment data must be bytes, not \'{}\''.format(data.__class__.__name__))
        self.contents.append(data)

class IMAPEmail:
    def __init__(self, message: email.message.Message):
        self.msgobj = message
        # print(email.header.decode_header(message['subject']))
        self.recipients = message.get('to', '').replace('\n', '').replace('\r', '').replace('\t', ' ').split(', ')
        self.sender = message.get('from', '')
        self.subject = self.soft_decode(message.get('subject', ''))
        self.date = message.get('date', '')
        self.cc = message.get('cc', '').replace('\n', '').replace('\r', '').replace('\t', ' ').split(', ')
        self.bcc = message.get('bcc', '').replace('\n', '').replace('\r', '').replace('\t', ' ').split(', ')
        self.attachments = self.resolve_attachments(message)
        self.body = self.decode_body(message)
        self.type = 'html' if isinstance(self.body, BeautifulSoup) else 'text'

    def __repr__(self):
        return 'Email "{}" with body of len {}'.format(self.subject, len(self.body))
    __str__ = __repr__

    def get_body(self):
        if self.type == 'html':
            return soup_without(self.body, name='style').text.strip()
        return self.body.strip()

    @staticmethod
    def soft_decode(string):
        s, enc = email.header.decode_header(string)[0]
        return s.strip() if enc is None else codecs.decode(s, enc).strip()

    @staticmethod
    def resolve_attachments(message: email.message.Message):
        attachments = []
        for part in message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            fileName = IMAPEmail.soft_decode(part.get_filename())
            if fileName:
                a = IMAPAttachment(IMAPEmail.soft_decode(fileName))
                a.write(part.get_payload(decode=True))
                attachments.append(IMAPAttachment)

        return attachments

    @staticmethod
    def decode_body(message: email.message.Message):
        # If the message comes in multiple portions (i.e. there are attachments)
        if message.is_multipart():
            for part in message.get_payload():
                # Throw away attachments
                if part.get_filename():
                    continue

                # Return an html object or plaintext
                charset = part.get_content_charset()
                if part.get_content_type() == 'text/plain':
                    return part.get_payload(decode=True).decode(charset).strip()
                if part.get_content_type() == 'text/html':
                    return html(part.get_payload(decode=True).decode(charset))
                # Note that we can just return because even though it's multipart, the only usual suspects for the parts are extra attachments, which we're avoiding.
        else:
            return message.get_payload(decode=True).decode(message.get_content_charset()).strip()

class Inbox:
    def __init__(self, email_address=USER, email_password=PASS):
        self.addr = email_address
        self.pwd = email_password
        self.messages = []

    def get_size(self):
        return len(self.messages)
    def get(self, i) -> IMAPEmail:
        if i < self.get_size():
            return self.messages[i]
        return None
    def fetch(self):
        self.messages = self._fetch_inbox(self.addr, self.pwd)

    @staticmethod
    def _fetch_inbox(addr=USER, pwd=PASS, debug=False):
        c = imaplib.IMAP4_SSL(IMAPHOST)
        if debug: print('Logging in...')
        c.login(addr, pwd)
        with c:
            msgs = []
            c.select('INBOX', readonly=True)
            _, [ids] = c.search(None, 'ALL')
            for msgid in ids.split():
                _, data = c.fetch(msgid, '(RFC822)')
                for response_part in data:
                    if isinstance(response_part, tuple):
                        msgs.append(IMAPEmail(email.message_from_bytes(response_part[1])))
            return msgs


if __name__ == '__main__':
    #inbox = Inbox(USER, PASS)
    #inbox.fetch()
    #print(inbox.get(0).get_body())

    smtp = Remote()
    #e = Email('ykey-cohen@emeryweiner.org', subject='Hello')
    #e.write('Hello')
    #smtp.send(e)

    #832-258-9790att
    m = MMS(('917-549-2662', 'sprint'))
    # m.write('This is a test of Salus\' new text automation system.\nDo not attempt to respond.')
    m.attach('web/assets/image/speaker.jpg')
    smtp.send(m)
    smtp.close()
