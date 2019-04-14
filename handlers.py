from response import Request, Response

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

    @staticmethod
    def handler(f):
        def wrapper(*args):
            if f(*args) is not None:
                return None
            return args[0].response
        return wrapper


class DefaultHandler(RequestHandler):
    @RequestHandler.handler
    def call(self):
        self.response.set_body("<html><form method=\"POST\"><input type=\"text\" name=\"test\"><input type=\"submit\"></form></html>", ctype='html')
        if self.request.get_cookie('hello') is None:
            self.response.add_cookie('hello', 'world')
        #self.response.attach_file('/'.join(self.request.address), rendr=True, rendrtypes=('html', 'htm', 'js', 'css'),
        #                    nb_page='account/dashboard/index.html')#'/'.join(self.request.address))


# Handlers
class HandlerBlank(RequestHandler):
    @RequestHandler.handler
    def call(self):
        self.response.redirect('/home/index.html')

class HandlerHome(RequestHandler):
    @RequestHandler.handler
    def call(self):
        ...


GET = {
    '/': DefaultHandler,
    '/reboot': HandlerReboot,
}

POST = {

}

INDEX = {}
INDEX.update(GET)
INDEX.update(POST)