from response import Request, Response
from client import ClientObj

class RequestHandler:
    def __init__(self, request: Request, response: Response):
        self.request = request
        self.response = response
        self.path = self.request.path
        self.microserver = self.request.req.server
        self.server = self.microserver.macroserver
        self.c_ip, self.c_port = self.request.req.client_address
        self.ip = self.request.server.host
        self.port = self.request.server.port
        self.request.client = ClientObj(self.request.addr[0], self.request.get_cookie('user_token'))
        self.response.client = self.client = self.request.client
        self.response.add_cookie('user_token', self.client.account.new_key() if self.client.account is not None else '_none')

    @staticmethod
    def handler(f):
        def wrapper(*args):
            if f(*args) is not None:
                return None
            return args[0].response
        return wrapper


class DefaultHandler(RequestHandler):
    def call(self):
        self.response.set_body("<html><form method=\"POST\"><input type=\"text\" name=\"test\"><input type=\"submit\"></form></html>", ctype='html')
        #self.response.attach_file('/'.join(self.request.address), rendr=True, rendrtypes=('html', 'htm', 'js', 'css'),
        #                    nb_page='account/dashboard/index.html')#'/'.join(self.request.address))


# Handlers
class HandlerBlank(RequestHandler):
    def call(self):
        self.response.redirect('/home/index.html')

class HandlerReboot(RequestHandler):
    def call(self):
        self.server.reboot()

class HandlerHome(RequestHandler):
    def call(self):
        ...

class HandlerSignupPage(RequestHandler):
    def call(self):
        self.response.set_body(
            "<html><form method=\"POST\" action=\"/login\">Username<br><input type=\"text\" name=\"name\"><br>Password<br><input type=\"password\" name=\"pwd\"><br><input type=\"submit\"></form></html>",
            ctype='html')

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


GET = {
    '/': DefaultHandler,
    '/reboot': HandlerReboot,
    '/signup': HandlerSignupPage,
    '/protected': HandlerProtectedTest,
}

POST = {
    '/login': HandlerSignup
}

INDEX = {}
INDEX.update(GET)
INDEX.update(POST)
