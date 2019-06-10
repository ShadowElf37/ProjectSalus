from server.env import EnvReader
from scrape import html, soup_without
from bs4 import BeautifulSoup
from server.threadpool import Pool, Poolsafe

ENV = EnvReader('main.py')

SMTPHOST = 'smtp.office365.com:587'
IMAPHOST = 'outlook.office365.com'

USER = ENV.get('EMAIL')
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

    def compile(self):
        return self.mime.as_string()


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

    def __init__(self, *recipients, sender=USER, group=False):
        """Give recipients as tuples with (number, service provider)"""
        if type(recipients[0]) not in (tuple, list):
            raise TypeError('Recipients for MMS must be (number, provider) tuples')
        self.recipients = [r[0].replace('-', '')+MMS.PROVIDERS[r[1]] for r in recipients]
        super().__init__(sender, *self.recipients)
        self.group = group

    def compile(self):
        self.mime['From'] = self.sender
        if self.group:
            self.mime['To'] = ', '.join((self.recipients))
        else:
            self.mime['To'] = ''
            self.mime['Bcc'] = ', '.join(self.recipients)
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
    def __init__(self, message: email.message.Message, uid=None, index=None):
        self.msgobj = message
        # print(email.header.decode_header(message['subject']))
        self.uid = uid
        self.index = index
        self.recipients = message.get('to', '').replace('\n', '').replace('\r', '').replace('\t', ' ').split(', ')
        self.sender = message.get('from', '')
        self.subject = self.soft_decode(message.get('subject', ''))
        self.date = message.get('date', '')
        self.cc = message.get('cc', '').replace('\n', '').replace('\r', '').replace('\t', ' ').split(', ')
        self.bcc = message.get('bcc', '').replace('\n', '').replace('\r', '').replace('\t', ' ').split(', ')
        self.server_uid = message.get('message-id', '').strip()
        self.attachments = self.resolve_attachments(message)
        self.body = self.decode_body(message)
        self.type = 'html' if isinstance(self.body, BeautifulSoup) else 'text'

    def __repr__(self):
        return 'Email from {} to {} with subject "{}".\nSent with {} attachments and body of length {}.\nCc\'d to {}.\nTimestamped "{}".\nID: {}'.format(
            self.sender, self.recipients, self.subject, len(self.attachments), len(self.body), self.cc, self.date, self.uid)

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
                attachments.append(a)

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
                # Note that we can just return because even though it's multipart, the only usual suspects for the multiple parts are extra attachments, which we're avoiding.
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
    def fetch(self, max_count=10, threadpool: Pool=None, wait_for_pool=True):
        self.messages = Inbox._fetch_inbox(self.addr, self.pwd, max_count=max_count, threadpool=threadpool, wait_for_pool=wait_for_pool)
        return self.messages

    @staticmethod
    def _fetch_inbox(addr=USER, pwd=PASS, max_count=10, threadpool: Pool=None, wait_for_pool=True, debug=False):
        c = imaplib.IMAP4_SSL(IMAPHOST)
        if debug: print('Logging in...')
        c.login(addr, pwd)
        with c:
            msgs = []
            c.select('INBOX', readonly=True)
            _, [ids] = c.uid('SEARCH', 'ALL')
            for i, msgid in enumerate(ids.split()):
                if i == max_count:
                    break
                if threadpool:
                    msg = Poolsafe(Inbox._fetch_msg, c, msgid, i+1)
                    threadpool.pushps(msg)
                else:
                    msg = Inbox._fetch_msg(c, msgid, i+1)
                msgs.append(msg)

            if threadpool and wait_for_pool:
                msgs = [ps.wait() for ps in msgs]
            return msgs

    @staticmethod
    def _fetch_msg(conn, id, index):
        _, data = conn.uid('fetch', id, '(RFC822)')
        for response_part in data:
            if isinstance(response_part, tuple):
                return IMAPEmail(email.message_from_bytes(response_part[1]), id, index)



if __name__ == '__main__':
    print('Logging in...')
    inbox = Inbox(USER, PASS)
    testpool = Pool(20)
    testpool.launch()
    print('Fetching...')
    inbox.fetch(1, threadpool=testpool, wait_for_pool=True)
    print('Fetched.')
    print(inbox.get(0))

    #smtp = Remote()
    #e = Email('ykey-cohen@emeryweiner.org', subject='Hello')
    #e.write('Hello')
    #smtp.send(e)

    #832-258-9790att

    exit()

    smtp = Remote()
    m = MMS(
        #('832-258-9790', 'att'),
        #('713-325-3232', 'verizon'),
        #('832-767-9123', 'att')
        #('832-499-8020', 'att')
        )
    # m.write('This is a test of Salus\' new text automation system.\nDo not attempt to respond.')
    m.attach('web/assets/image/speaker.jpg')
    # m.attach('README.md')
    # m.attach('_main.py')
    from datetime import datetime
    m.write(datetime.now().strftime('Good morning.\nIt is currently %-I:%M %p\n\t- Salus'))
    smtp.send(m)
    smtp.close()
