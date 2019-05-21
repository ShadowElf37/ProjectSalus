from server.response import Request, Response
from server.client import ClientObj, Account, ShellAccount
import server.client
from server.config import get_config
from server.crypt import *

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
        if name not in updates.DIRECTORY:
            self.response.refuse()
            return
        password = self.request.get_post('pwd')
        a = self.client.create_account(name, password)
        a.password_enc = permahash(password)
        print(a.password, a.password_enc)
        self.response.add_cookie('user_token', a.key, samesite='strict', path='/')
        # print('$$$', self.response.cookie['user_token'])
        self.response.redirect('/home/index.html')

class HandlerLogin(RequestHandler):
    def call(self):
        name = self.request.get_post('name')
        password = self.request.get_post('pwd')
        pe = permahash(password)
        self.client.login(name, pe)
        account = self.client.account
        account.password = password
        if account.bb_auth == ('', '') and account.bb_enc != ('', ''):
            account.bb_auth = map(lambda l: unhashints(l, account.password), account.bb_enc)
        self.response.add_cookie('user_token', account.key, samesite='strict', path='/')
        if self.client.is_real():
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


import updates
import scrape
from server.threadpool import Poolsafe
class HandlerBBPage(RequestHandler):
    def call(self):
        if self.rank < 1:
            self.response.redirect('/login')
            return
        self.response.attach_file('/accounts/bb_login.html')

class HandlerBBLogin(RequestHandler):
    def call(self):
        self.account.bb_auth = self.request.get_post('user'), self.request.get_post('pass')
        self.account.bb_enc = hashstr(self.request.get_post('user'), self.account.password), hashstr(self.request.get_post('pass'), self.account.password)
        self.account.profile = updates.DIRECTORY[self.account.name]
        self.response.redirect('/bb')

class HandlerBBInfo(RequestHandler):
    def call(self):
        if self.rank < 1:
            self.response.refuse()
            return
        self.account.bb_id = self.account.profile['id']

        schedule = self.account.bb_cache.get('schedule')
        if not schedule:
            schedule = updates.register_bb_updater(self.account, 'schedule', scrape.BlackbaudScraper.schedule, ((updates.FUNC, scrape.todaystr),), 120).wait()

        assignments = self.account.bb_cache.get('assignments')
        if not assignments:
            assignments = updates.register_bb_updater(self.account, 'assignments', scrape.BlackbaudScraper.assignments, (), 30).wait()

        grades = self.account.bb_cache.get('grades')
        if not grades:
            grades = updates.register_bb_updater(self.account, 'grades', scrape.BlackbaudScraper.grades, (self.account.bb_id,), 30).wait()

        self.response.attach_file('/accounts/bb_test.html',
                                  profile=scrape.prettify(self.account.profile).replace('\n', '<br>'),
                                  schedule='<br>'.join(schedule.keys()),
                                  assignments='<br>'.join(assignments.keys()),
                                  grades='<br>'.join([k + ' - ' + str(grades[k]['average']) for k in grades.keys()]),
                                  menu='<br>'.join(updates.SAGEMENU[scrape.todaystr()]))


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
