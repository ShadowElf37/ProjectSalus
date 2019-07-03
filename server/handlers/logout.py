from .base import *

class HandlerLogout(RequestHandler):
    def call(self):
        self.response.add_cookie('user_token', None)
        self.response.redirect('/accounts/login.html')
        updates.chronomancer.clean(self.account.name)
