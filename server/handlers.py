from server.response import Request, Response
from server.client import ClientObj
import os.path as op

class RequestHandler:
    def __init__(self, request: Request, response: Response):
        self.request = request
        self.response = response
        self.path = self.request.path
        self.server = self.request.req.server
        self.c_ip, self.c_port = self.request.req.client_address
        self.ip = self.request.server.host
        self.port = self.request.server.port
        self.token = self.request.get_cookie('user_token')
        self.make_client()

    def make_client(self):
        self.response.client = self.client = self.request.client = ClientObj(self.request.addr[0], self.token)
        self.response.add_cookie('user_token',
                                 self.client.account.new_key() if self.client.account is not None else '_none',
                                 'httponly', path='/')

    @staticmethod
    def handler(f):
        def wrapper(*args):
            if f(*args) is not None:
                return None
            return args[0].response
        return wrapper


class DefaultHandler(RequestHandler):
    def call(self):
        self.response.attach_file(self.path)
        # self.response.set_body("<html><form method=\"POST\"><input type=\"text\" name=\"test\"><input type=\"submit\"></form></html>", ctype='text/html')
        #self.response.attach_file('/'.join(self.request.address), rendr=True, rendrtypes=('html', 'htm', 'js', 'css'),
        #                    nb_page='account/dashboard/index.html')#'/'.join(self.request.address))


# Important universal handlers

class HandlerBlank(RequestHandler):
    def call(self):
        self.response.redirect('/test/index.html')

class HandlerReboot(RequestHandler):
    def call(self):
        self.response.set_body('Server rebooting.')
        self.server.reboot()


# Project-specific handlers

class HandlerHome(RequestHandler):
    def call(self):
        ...

class HandlerReadme(RequestHandler):
    def call(self):
        self.response.attach_file('/../README.md')

class HandlerSignupPage(RequestHandler):
    def call(self):
        self.response.set_body(
            "<html><form method=\"POST\" action=\"/signup\">Username<br><input type=\"text\" name=\"name\"><br>Password<br><input type=\"password\" name=\"pwd\"><br><input type=\"submit\"></form></html>",
            ctype='text/html')

class HandlerLoginPage(RequestHandler):
    def call(self):
        self.response.set_body(
            "<html><form method=\"POST\" action=\"/login\">Username<br><input type=\"text\" name=\"name\"><br>Password<br><input type=\"password\" name=\"pwd\"><br><input type=\"submit\"></form></html>",
            ctype='text/html')

class HandlerProtectedTest(RequestHandler):
    def call(self):
        if self.client.validate_account():
            self.response.set_body('hello {}!'.format(self.client.account.name))
        else:
            self.response.set_body('bye bye!')

class HandlerSignup(RequestHandler):
    def call(self):
        name = self.request.get_post('name')
        password = self.request.get_post('pwd')
        self.client.create_account(name, password)
        self.response.add_cookie('user_token', self.client.account.key)
        self.response.redirect('/', get=True)

class HandlerLogin(RequestHandler):
    def call(self):
        name = self.request.get_post('name')
        password = self.request.get_post('pwd')
        self.client.login(name, password)
        self.response.add_cookie('user_token', self.client.account.key)
        self.response.redirect('/', get=True)

class HandlerLogout(RequestHandler):
    def call(self):
        self.response.add_cookie('user_token', None)
        self.response.redirect('/', get=True)

class HandlerTestPage(RequestHandler):
    def call(self):
        self.response.attach_file('web/test/index.html')

GET = {
    '/': HandlerBlank,
    '/reboot': HandlerReboot,
    '/signup': HandlerSignupPage,
    '/login': HandlerLoginPage,
    '/protected': HandlerProtectedTest,
    '/test': HandlerTestPage,
    '/logout': HandlerLogout,
    '/readme': HandlerReadme,
    #'/home/index.html': ...
}

POST = {
    '/signup': HandlerSignup,
    '/login': HandlerLogin
}

INDEX = {}
INDEX.update(GET)
INDEX.update(POST)
