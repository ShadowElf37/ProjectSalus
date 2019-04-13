class RequestHandler:
    def __init__(self, request, response):
        self.request = request
        self.response = response
        self.path = self.request.path
        self.server = self.request.req.server
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

        self.response.set_body('Testing 123.')
        #self.response.attach_file('/'.join(self.request.address), rendr=True, rendrtypes=('html', 'htm', 'js', 'css'),
        #                    nb_page='account/dashboard/index.html')#'/'.join(self.request.address))



# Handlers
class HandlerBlank(RequestHandler):
    @RequestHandler.handler
    def call(self):
        self.response.set_status_code(307, location='/home/index.html')


class HandlerHome(RequestHandler):
    @RequestHandler.handler
    def call(self):
        self.response.attach_file('home/index.html', nb_page='home/index.html')


GET = {
    '': HandlerBlank,
    'home/index.html': HandlerHome,
}

POST = {

}

INDEX = {}
INDEX.update(GET)
INDEX.update(POST)