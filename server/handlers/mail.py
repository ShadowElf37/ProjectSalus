from .base import *
from urllib.parse import unquote, unquote_to_bytes

class HandlerMailPage(RequestHandler):
    def call(self):
        self.response.redirect('/myday')
        return
        messages = [msg.body for msg in self.account.inbox.messages]
        self.response.attach_file('/accounts/mail.html', messages='<br><br>'.join(messages))

class HandlerSendMail(RequestHandler):
    def call(self):
        if self.account.has_inbox():
            to = [s for s in [s.strip() for s in self.request.get_post('to').split(',')] if s]
            subject = self.request.get_post('subject')
            body = self.request.get_post('body')

            attachments = self.request.get_post('attachments')
            attachment_data = self.request.get_post('_attachments')
            if type(attachments) is str:
                attachments = [attachments]
            if type(attachment_data) is str:
                attachment_data = [attachment_data]
            print(attachments)
            print(attachment_data[0].replace('%', ' %').replace('\n', '    '))

            msg = mail.Email(self.account.email, *to, subject=subject)
            msg.write(body)

            if attachments and attachment_data:
                for i,a in enumerate(attachments):
                    print(unquote(a), unquote_to_bytes(attachment_data[i]))
                    msg._attach(unquote(a), unquote_to_bytes(attachment_data[i]))

            self.response.set_body('Done.')
            try:
                remote = mail.SMTPRemote(self.account.email, self.account.inbox.auth.password)
                remote.send(msg)
            except Exception as e:
                self.server.log('SMTP exception thrown - %s: %s' % (str(e), str(e.args)))
                self.response.set_body('An error occurred.', append=False)
        else:
            self.response.send_error(403, 'An inbox has not been generated for this account yet. Please contact Yovel or a high-level SGA representative if you believe this was an error.')
