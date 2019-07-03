from .base import *

class HandlerTestPage(RequestHandler):
    def call(self):
        self.response.attach_file('/test/index.html')
