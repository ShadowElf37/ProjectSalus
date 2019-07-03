from .base import *

class HandlerHome(RequestHandler):
    def call(self):
        self.response.attach_file('/home/index.html')
