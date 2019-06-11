from server.env import EnvReader
from scrape import html, soup_without
from bs4 import BeautifulSoup
from server.threadpool import Pool, Poolsafe
from random import choice as rchoice

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
    def __init__(self, message: email.message.Message, uid=None):
        self.msgobj = message
        # print(email.header.decode_header(message['subject']))
        self.uid = uid
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
        return '<Email "{}" (len {}) ({} attachments) from {}>'.format(
            self.subject, len(self.body), len(self.attachments), self.sender)

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
        self.uids = []

    def get_size(self):
        return len(self.messages)
    def update_uids(self):
        self.uids = [msg.uid for msg in self.messages if isinstance(msg, IMAPEmail)]

    def get(self, i) -> IMAPEmail:
        if i < self.get_size():
            return self.messages[i]
        return None
    def get_uid(self, uid) -> IMAPEmail:
        return next(filter(lambda m: m.uid == str(uid).encode(), self.messages), None)
    def get_all(self) -> [IMAPEmail]:
        return self.messages

    def random_msg(self) -> IMAPEmail:
        return rchoice(self.messages)
    def random_uid(self):
        return rchoice(self.uids)

    def new_conn(self):
        c = imaplib.IMAP4_SSL(IMAPHOST)
        c.login(self.addr, self.pwd)
        return c

    def pull(self, uid, inbox='INBOX', headeronly=False):
        return self._fetch_msg(Inbox._selected(self.new_conn(), inbox), uid, headeronly=headeronly)

    # Fetch first max_count messages from server irrespective of whether or not they've been downloaded
    def fetch(self, inbox_name='INBOX', max_count=10, threadpool: Pool=None, wait_for_pool=True):
        self.messages = Inbox._fetch_inbox(self.addr, self.pwd, inbox_name=inbox_name, max_count=max_count, threadpool=threadpool, wait_for_pool=wait_for_pool)
        self.update_uids()
        return self.messages

    # Get all messages that we don't have up to max_count (max_count counting from server)
    def search_new(self, inbox_name='INBOX', max_count=10):
        return [uid for uid in self._search_inbox(self.new_conn(), inbox_name)[:max_count] if uid not in self.uids]
    # Get all messages that aren't on the server anymore
    def search_stale(self, inbox_name='INBOX'):
        return [uid for uid in self.uids if uid not in self._search_inbox(self.new_conn(), inbox_name)]

    # Remove messages from here that can't be found in the inbox anymore
    def clear_stale(self, inbox_name='INBOX'):
        for uid in self.search_stale(inbox_name):
            self.messages.remove(self.get_uid(uid))

    # Get messages up to max_count from server that HAVEN'T been downloaded yet
    def update(self, inbox_name='INBOX', max_count=10, threadpool: Pool=None):
        if not threadpool:
            masterconn = self.new_conn()
        poolsafes = []

        for uid in self.search_new(max_count=max_count):
            if threadpool:
                ps = Poolsafe(Inbox._fetch_msg_newc, self.addr, self.pwd, uid, folder=inbox_name)
                threadpool.pushps(ps)
                poolsafes.append(ps)
            else:
                msg = Inbox._fetch_msg(masterconn, uid)
                self.messages.append(msg)

        for ps in poolsafes:
            self.messages.append(ps.wait())
        self.messages.sort(key=lambda m: m.date)
        self.update_uids()
        return self.messages

    @staticmethod
    def _selected(c, inbox):
        c.select(inbox, readonly=True)
        return c

    # Get message UIDs
    @staticmethod
    def _search_inbox(conn, folder='INBOX'):
        conn.select(folder, readonly=True)
        _, [ids] = conn.uid('SEARCH', 'ALL')
        return ids.split()

    # Fetch entire inbox of any user, up to max_count messages
    @staticmethod
    def _fetch_inbox(addr=USER, pwd=PASS, inbox_name='INBOX', max_count=10, threadpool: Pool=None, wait_for_pool=True, debug=False):
        c = imaplib.IMAP4_SSL(IMAPHOST)
        if debug: print('Logging in...')
        c.login(addr, pwd)
        with c:
            msgs = []
            ids = Inbox._search_inbox(c, inbox_name)
            for i, msgid in enumerate(ids):
                if i == max_count:
                    break
                if threadpool:
                    msg = Poolsafe(Inbox._fetch_msg_newc, addr, pwd, msgid, i+1, folder=inbox_name)
                    threadpool.pushps(msg)
                else:
                    msg = Inbox._fetch_msg(c, msgid)
                msgs.append(msg)

            if threadpool and wait_for_pool:
                msgs = [ps.wait() for ps in msgs]
            return msgs

    # Create a new connection and fetch from server by uid
    @staticmethod
    def _fetch_msg_newc(addr, pwd, id, folder='INBOX', headeronly=False):
        c = imaplib.IMAP4_SSL(IMAPHOST)
        c.login(addr, pwd)
        c.select(folder, readonly=True)
        return Inbox._fetch_msg(c, id, headeronly=headeronly)

    # Use an existing connection to fetch from server by uid
    @staticmethod
    def _fetch_msg(conn, id, headeronly=False):
        _, data = conn.uid('fetch', id, '(RFC822)' if not headeronly else '(BODY.PEEK[HEADER])')
        for response_part in data:
            if isinstance(response_part, tuple):
                return IMAPEmail(email.message_from_bytes(response_part[1]), id)



if __name__ == '__main__':
    print('Logging in...')
    inbox = Inbox(USER, PASS)
    testpool = Pool(20)
    testpool.launch()
    print('Fetching...')
    inbox.update(threadpool=testpool)
    print('Fetched.')
    print(inbox.get_all())

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
