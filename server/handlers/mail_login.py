from .base import *

class HandlerMailLoginPage(RequestHandler):
    def call(self):
        if self.rank < 1:
            self.response.redirect('/login')
            return
        if self.account.inbox and self.account.inbox.auth.decrypted:
            self.response.redirect('/mail')
            return
        self.response.attach_file('/accounts/mail_login.html')

class HandlerMailLogin(RequestHandler):
    def call(self):
        pwd = self.request.get_post('pass')
        user = self.account.email
        encoder = cryptrix(self.account.password, self.account.name)

        creds = Credentials(user, pwd, encoder)

        session = mail.Inbox(creds)
        try:
            session.new_conn()
            session.update(threadpool=updates.updater_pool)
        except mail.imaplib.IMAP4.error:
            creds.dump()
            self.response.refuse('Incorrect password, or your email stored on Blackbaud is incorrect. If this error occurs outside of testing then Yovel is dumb and tell him immediately.')
            return

        self.account.inbox = session
        self.response.redirect('/mail', get=True)