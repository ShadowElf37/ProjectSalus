from server.response import Request, Response
from server.client import ClientObj, Account, ShellAccount
import server.client
from server.config import get_config

navbar = get_config('navbar')

class RequestHandler:
    def __init__(self, request: Request, response: Response):
        self.request = request
        self.response = response
        self.path: str = self.request.path
        self.server = self.request.req.server
        self.c_ip, self.c_port = self.request.req.client_address
        self.ip = self.request.server.host
        self.port = self.request.server.port
        self.token: str = self.request.get_cookie('user_token')
        self.account = ShellAccount()
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
        self.account: Account  = self.client.account
        self.response.add_cookie('user_token', self.account.key, samesite='strict', path='/')

    def pre_call(self):
        # For debug - remove and put only in rank 4 later
        self.render_register(
            reboot_controls='\n'.join([
                '<button type="button" class="ctrl-button" onclick="sendControlKey(\'{1}\')">{0}</button>'.format(i,j) for i,j in
                {
                    'Update': 'update',
                    'Reboot': 'reboot',
                    'Clear Config': 'refresh-config',
                    'Clear Cache': 'refresh-cache',
                    'Update and Restart': 'update-reboot',
                    'Shutdown': 'shutdown',
                }.items()])
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
        ...


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

class HandlerLog(RequestHandler):
    def call(self):
        self.response.set_body(self.server.get_log())

class HandlerControlWords(RequestHandler):
    def call(self):
        self.response.set_body('0')
        cmd = self.request.get_post('cmd')

        self.response.add_cookie('user_token', self.token, samesite='strict', path='/')
        self.account.manual_key(self.token)

        # if self.rank >= 4:
        if cmd == 'reboot':
            self.server.log('Request to reboot granted.')
            self.server.reboot()
        elif cmd == 'refresh-cache':
            self.server.log('Request to refresh server cache granted.')
            self.server.reload_cache()
        elif cmd == 'refresh-config':
            self.server.log('Request to reload config granted.')
            self.server.reload_config()
        elif cmd == 'update':
            self.server.log('Request to update granted.')
            self.server.update()
        elif cmd == 'update-reboot':
            self.server.log('Request to update and reboot granted.')
            self.server.update()
            self.server.reboot()
        elif cmd == 'shutdown':
            self.server.shutdown()
        else:
            self.server.log('An unknown control word was received:', cmd)

# Project-specific handlers

class HandlerHome(RequestHandler):
    def call(self):
        self.response.attach_file('/home/index.html')

class HandlerSignupPage(RequestHandler):
    def call(self):
        self.response.attach_file('/accounts/signup.html')

class HandlerLoginPage(RequestHandler):
    def call(self):
        self.response.attach_file('/accounts/login.html')

class HandlerSignup(RequestHandler):
    def call(self):
        name = self.request.get_post('name')
        password = self.request.get_post('pwd')
        a = self.client.create_account(name, password)
        self.response.add_cookie('user_token', a.key, samesite='strict', path='/')
        # print('$$$', self.response.cookie['user_token'])
        self.response.redirect('/home/index.html')

class HandlerLogin(RequestHandler):
    def call(self):
        name = self.request.get_post('name')
        password = self.request.get_post('pwd')
        self.client.login(name, password)
        self.response.add_cookie('user_token', self.client.account.key, samesite='strict', path='/')
        if self.client.is_real():
            # print('@', self.client.account.key)
            self.response.redirect('/home/index.html')
        else:
            self.response.redirect('/accounts/login.html')

class HandlerLogout(RequestHandler):
    def call(self):
        self.response.add_cookie('user_token', None)
        self.response.redirect('/accounts/login.html')

class HandlerTestPage(RequestHandler):
    def call(self):
        self.response.attach_file('/test/index.html')


class HandlerAdminBoard(RequestHandler):
    def call(self):
        if self.rank >= 4:
            self.response.attach_file('/admin/controlboard.html')
        else:
            self.response.refuse()


import scrapes
import scrape
class HandlerBBPage(RequestHandler):
    def call(self):
        if self.rank < 1:
            self.response.redirect('/login')
            return
        self.response.attach_file('/accounts/bb_login.html')

class HandlerBBLogin(RequestHandler):
    def call(self):
        self.account.bb_user = self.request.post_vals['user']
        self.account.bb_pass = self.request.post_vals['pass']
        self.account.profile = scrapes.DIRECTORY[self.account.name]
        self.response.redirect('/bb', get=True)

class HandlerBBInfo(RequestHandler):
    def call(self):
        if self.rank < 1:
            self.response.refuse()
            return
        session = scrape.BlackbaudScraper()
        print(self.account.bb_user, self.account.bb_pass, self.account.name)
        session.login(self.account.bb_user, self.account.bb_pass, 't')
        uid = self.account.profile['id']
        self.response.attach_file('/accounts/bb_test.html', schedule=scrape.prettify(session.schedule('05/20/2019')).replace('\n', '<br>'))


GET = {
    '/': HandlerBlank,
    '/accounts/signup.html': HandlerSignupPage,
    '/accounts/login.html': HandlerLoginPage,
    '/login': HandlerLoginPage,
    '/home/index.html': HandlerHome,
    '/test': HandlerTestPage,
    '/logout': HandlerLogout,
    '/logfile': HandlerLog,
    '/bb_login': HandlerBBPage,
    '/bb': HandlerBBInfo,
}

POST = {
    '/signup': HandlerSignup,
    '/login': HandlerLogin,
    '/ctrl-words': HandlerControlWords,
    '/bb_post': HandlerBBLogin
}

INDEX = {}
INDEX.update(GET)
INDEX.update(POST)
