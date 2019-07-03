from .base import *

class HandlerSignupPage(RequestHandler):
    def call(self):
        self.response.attach_file('/accounts/signup.html')

class HandlerSignup(RequestHandler):
    def call(self):
        name = self.request.get_post('name')

        if name not in updates.DIRECTORY:
            self.response.refuse('%s is not whitelisted.' % name)
            return
        if user_tokens.find(lambda a: a.name == name):
            self.response.redirect('/login')
            return

        password = self.request.get_post('pwd')
        account = self.client.create_account(name, password)
        account.password_enc = hash(password, self.client.account.name)

        self.response.add_cookie('user_token', account.key, samesite='strict', path='/')

        account.dir = updates.DIRECTORY[account.name]
        account.bb_id = account.dir['id']
        account.email = account.dir.get('email')

        self.response.redirect('/home')
