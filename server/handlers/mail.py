from .base import *

class HandlerMailPage(RequestHandler):
    def call(self):
        messages = [msg.body for msg in self.account.inbox.messages]
        self.response.attach_file('/accounts/mail.html', messages='<br><br>'.join(messages))

class HandlerSendMail(RequestHandler):
    def call(self):
        if self.account.has_inbox():
            to = [s for s in [s.strip() for s in self.request.get_post('to').split(',')] if s]
            subject = self.request.get_post('subject')
            body = self.request.get_post('body')

            attachments = self.request.get_post('attachments')
            print(attachments)

            msg = mail.Email(self.account.email, *to, subject=subject)
            msg.write(body)

            self.response.set_body('Done.')
            try:
                remote = mail.SMTPRemote(self.account.email, self.account.inbox.auth.password)
                remote.send(msg)
            except Exception as e:
                self.server.log('SMTP exception thrown - %s: %s' % (str(e), str(e.args)))
                self.response.set_body('An error occurred.', append=False)
        else:
            self.response.send_error(403, 'An inbox has not been generated for this account yet. Please contact Yovel or a high-level SGA representative if you believe this was an error.')
