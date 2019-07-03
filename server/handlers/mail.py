from .base import *

class HandlerMailPage(RequestHandler):
    def call(self):
        messages = [msg.body for msg in self.account.inbox.messages]
        self.response.attach_file('/accounts/mail.html', messages='<br><br>'.join(messages))

class HandlerSendMail(RequestHandler):
    def call(self):
        to = self.request.get_post('to')
        body = self.request.get_post('body')

        msg = mail.Message(self.account.email, *to)
        msg.write(body.encode())

        self.response.set_body('Done.')
        try:
            remote = mail.SMTPRemote(self.account.email, self.account.inbox.pwd)
            remote.send(msg)
        except:
            self.response.set_body('An error occurred.', append=False)