from .base import *

class HandlerDirectory(RequestHandler):
    def call(self):
        self.response.attach_file('/accounts/directory.html', students=updates.DIRECTORY_HTML, teachers=updates.TEACHER_HTML)