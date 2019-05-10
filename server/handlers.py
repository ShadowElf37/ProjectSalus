from server.response import Request, Response
from server.client import ClientObj
from server.config import get_config
import os.path as op

navbar = get_config('navbar')

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
        self.load_client()
        self.rank = 0
        if self.account:
            self.rank = self.account.rank
        self.render_register(
            name=self.account.name,
            test='hello',
            themeblue='#0052ac',
            themedarkblue='#00429c',
            themeoffwhite='#eeeeee',
            themegrey='#cccccc',
            navbar='\n'.join(['<li{}><a{}>{}</a></li>'.format(' class="active"' if self.path == li[1] else ' class="disabled"' if li[2] else '', (' href="'+li[1]+'"') if not li[2] else '', li[0]) for li in navbar.get(self.rank)]),
            reboot_controls=''
        )
        # self.server.cache.reload()

    def render_register(self, **kwargs):
        self.response.default_renderopts.update(**kwargs)

    def load_client(self):
        self.response.client = self.client = self.request.client = ClientObj(self.request.addr[0], self.token)
        self.account = self.client.account
        self.response.add_cookie('user_token',
                                 self.account.new_key() if self.account.is_real() else '_none',
                                 'httponly', samesite='strict', path='/')

    def pre_call(self):
        # For debug - remove and put only in rank 4 later
        self.render_register(
            reboot_controls='\n'.join([
                '<button type="button" class="ctrl-button" onclick="return \"{}\"">{}</button>'.format(j,i) for i,j in
                (('Update', 'update'), ('Reboot', 'reboot'), ('Clear Config', 'refresh-config'), ('Clear Cache', 'refresh-cache'))])
        )

        if self.rank == 0:
            ...
        elif self.rank == 1:
            ...
        elif self.rank == 2:
            ...
        elif self.rank == 3:
            ...
        elif self.rank == 4:
            self.render_register(
                reboot_controls='\n'.join('<button type="button" class="ctrl-button" onclick="void(0);">{}</button>'.format(i) for i in ('Reboot', 'Clear Config', 'Clear Cache'))
            )

    def post_call(self):
        r = self.request
        if r.get_query:
            a = r.get_query.get('action')
            if a is not None and self.rank >= 4:
                ...
                #self.server.finish_request(r.req, r.addr)
                #self.server.shutdown_request(r.req)
                #if a == 'reboot':




class DefaultHandler(RequestHandler):
    def call(self):
        self.response.attach_file(self.path, cache=False)
        # self.response.set_body("<html><form method=\"POST\"><input type=\"text\" name=\"test\"><input type=\"submit\"></form></html>", ctype='text/html')
        #self.response.attach_file('/'.join(self.request.address), rendr=True, rendrtypes=('html', 'htm', 'js', 'css'),
        #                    nb_page='account/dashboard/index.html')#'/'.join(self.request.address))


# Important universal handlers

class HandlerBlank(RequestHandler):
    def call(self):
        self.response.redirect('/home/index.html')

class HandlerReboot(RequestHandler):
    def call(self):
        self.server.reboot()

class HandlerUpdate(RequestHandler):
    def call(self):
        self.server.update()

class HandlerRefreshConfig(RequestHandler):
    def call(self):
        self.server.reload_config()
        self.server.reload_cache()

class HandlerReloadCache(RequestHandler):
    def call(self):
        self.server.reload_cache()

class HandlerControlWords(RequestHandler):
    def call(self):
        self.response.set_body('0')
        cmd = self.request.get_post('cmd')
        if cmd == 'reboot':
            self.server.reboot()
        elif cmd == 'refresh-cache':
            self.server.reload_cache()
        elif cmd == 'refresh-config':
            self.server.reload_config()
        elif cmd == 'update':
            self.server.update()

# Project-specific handlers

class HandlerHome(RequestHandler):
    def call(self):
        self.response.attach_file('/home/index.html')

class HandlerReadme(RequestHandler):
    def call(self):
        self.response.attach_file('/../README.md')

class HandlerSignupPage(RequestHandler):
    def call(self):
        self.response.attach_file('/home/signup.html')

class HandlerLoginPage(RequestHandler):
    def call(self):
        self.response.attach_file('/home/login.html')

class HandlerProtectedTest(RequestHandler):
    def call(self):
        if self.account.is_real():
            self.response.set_body('hello {}!'.format(self.client.account.name))
        else:
            self.response.set_body('bye bye!')

class HandlerSignup(RequestHandler):
    def call(self):
        name = self.request.get_post('name')
        password = self.request.get_post('pwd')
        self.client.create_account(name, password)
        self.response.add_cookie('user_token', self.client.account.key)
        self.response.redirect('/home/index.html')

class HandlerLogin(RequestHandler):
    def call(self):
        name = self.request.get_post('name')
        password = self.request.get_post('pwd')
        self.client.login(name, password)
        self.response.add_cookie('user_token', self.client.account.key)
        if self.client.is_real():
            self.response.redirect('/home/index.html')
        else:
            self.response.redirect('/home/login.html')

class HandlerLogout(RequestHandler):
    def call(self):
        self.response.add_cookie('user_token', None)
        self.response.redirect('/home/login.html')

class HandlerTestPage(RequestHandler):
    def call(self):
        self.response.attach_file('/test/index.html')

GET = {
    '/': HandlerBlank,
    '/reboot': HandlerReboot,
    '/update': HandlerUpdate,
    '/cache': HandlerReloadCache,
    '/config': HandlerRefreshConfig,
    '/home/signup.html': HandlerSignupPage,
    '/home/login.html': HandlerLoginPage,
    '/home/index.html': HandlerHome,
    '/protected': HandlerProtectedTest,
    '/test': HandlerTestPage,
    '/logout': HandlerLogout,
    '/readme': HandlerReadme,
    # '/home/index.html': ...    remove default_handler from important pages like this
}

POST = {
    '/signup': HandlerSignup,
    '/login': HandlerLogin,
    '/ctrl-words': HandlerControlWords,
}

INDEX = {}
INDEX.update(GET)
INDEX.update(POST)
