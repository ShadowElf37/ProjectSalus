from .base import *

class HandlerSubmitPoll(RequestHandler):
    def call(self):
        print(self.request.post_vals)