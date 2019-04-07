class RequestHandler:
    def __init__(self, server, conn, addr, request, response):
        self.conn = conn
        self.addr = addr
        self.request = request
        self.response = response
        self.server = server

    def throwError(self, code, letter):
        self.response.error = self.server.throwError(code, letter, self.request.get_last_page(), self.conn, response=self.response)
        self.server.log.log(self.addr[0], 'threw error '+str(code)+letter,
                            lvl=Log.ERROR)
        return 1

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
        self.response.attach_file('/'.join(self.request.address), rendr=True, rendrtypes=('html', 'htm', 'js', 'css'),
                             nb_page='account/dashboard/index.html')#'/'.join(self.request.address))


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