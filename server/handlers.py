from .response import Request, Response
from .client import ClientObj, Account, ShellAccount, user_tokens
from .config import get_config
from .crypt import *
from html import escape
import updates
import scrape

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
        # For debug - remove and use admin board
        if self.account.name == 'Yovel Key-Cohen':
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
            ...

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
            self.response.refuse('%s is not whitelisted.' % name)
            return
        if user_tokens.find(lambda a: a.name == name):
            self.response.redirect('/accounts/login.html')
            return
        password = self.request.get_post('pwd')
        a = self.client.create_account(name, password)
        a.password_enc = hash(password, self.client.account.name)
        self.response.add_cookie('user_token', a.key, samesite='strict', path='/')
        self.account.profile = updates.DIRECTORY[self.account.name]
        # print('$$$', self.response.cookie['user_token'])
        self.response.redirect('/home/index.html')

class HandlerLogin(RequestHandler):
    def call(self):
        name = self.request.get_post('name')
        password = self.request.get_post('pwd')
        if not (name and password):
            self.response.back()
            return
        pe = hash(password, name)
        self.client.login(name, pe)
        account = self.client.account
        account.password = password
        if self.client.is_real():
            if account.bb_auth == ('', '') and account.bb_enc_pass != '':
                # If the account has cached passwords, load them with the key given
                decoder = cryptrix(account.password, account.name)
                account.bb_auth = decoder.decrypt(account.bb_enc_pass)
            self.response.add_cookie('user_token', account.key, samesite='strict', path='/')
            account.profile = updates.DIRECTORY[account.name]
            self.response.redirect('/home/index.html')
        else:
            self.response.redirect('/accounts/login.html')

class HandlerLogout(RequestHandler):
    def call(self):
        self.response.add_cookie('user_token', None)
        self.response.redirect('/accounts/login.html')
        updates.chronomancer.clean(self.account.name)

class HandlerTestPage(RequestHandler):
    def call(self):
        self.response.attach_file('/test/index.html')


class HandlerAdminBoard(RequestHandler):
    def call(self):
        if self.rank >= 4:
            self.response.attach_file('/admin/controlboard.html')
        else:
            self.response.refuse()

class HandlerBBPage(RequestHandler):
    def call(self):
        if self.rank < 1:
            self.response.redirect('/login')
            return
        if self.account.bb_auth == ('', ''):
            self.response.attach_file('/accounts/bb_login.html')
        else:
            self.response.redirect('/bb')

class HandlerBBLogin(RequestHandler):
    def call(self):
        # However, if the account has no cached passwords, cache it now
        encoder = cryptrix(self.account.password, self.account.name)
        if not self.request.get_post('pass'):
            self.response.back()
            return
        self.account.bb_enc = encoder.encrypt(self.request.get_post('pass'))
        self.account.bb_auth = self.account.profile.get('email'), self.request.get_post('pass')
        self.response.redirect('/bb')

class HandlerBBInfo(RequestHandler):
    def call(self):
        if self.rank < 1:
            self.response.refuse()
            return
        self.account.bb_id = self.account.profile['id']
        prf = updates.register_bb_updater(self.account, 'profile-details', scrape.BlackbaudScraper.dir_details, (self.account.bb_id,), updates.WEEKLY).wait()
        if prf is None:
            self.response.refuse('Invalid password for %s' % self.account.name)
            self.account.bb_enc = ''
            self.account.bb_auth = ('', '')
            return
        self.account.profile.update(prf)

        schedule = self.account.bb_cache.get('schedule')
        if not schedule:
            schedule = updates.register_bb_updater(self.account, 'schedule', scrape.BlackbaudScraper.schedule, ((updates.CALLABLE, scrape.todaystr),), 120)

        assignments = self.account.bb_cache.get('assignments')
        if not assignments:
            assignments = updates.register_bb_updater(self.account, 'assignments', scrape.BlackbaudScraper.assignments, (), 30)

        grades = self.account.bb_cache.get('grades')
        if not grades:
            grades = updates.register_bb_updater(self.account, 'grades', scrape.BlackbaudScraper.grades, (self.account.bb_id,), 60)

        if type(schedule) is not dict:
            schedule = schedule.wait()
        if type(assignments) is not dict:
            assignments = assignments.wait()
        if type(grades) is not dict:
            grades = grades.wait()
        #print(scrape.prettify(schedule))
        #print(scrape.prettify(assignments))
        #print(scrape.prettify(grades))

        classes = '\n'.join(["""<div class="class-tab">
                        <span class="period">{period}</span><span class="classname">{classname}</span>
                        <div class="dropdown">
                            <div class="grade">
                                <h3>Grade: {grade}</h3>
                                <p>{teacher}</p>
                                <p>{teacher_email}</p>
                            </div>
                            <ul class="assignments">
                                <h4 style="margin: 5px 0px 25px 0px">This Week's Assignments</h4>
                                {assignments}
                            </ul>
                        </div>
                    </div>""".format(
            period=c,
            classname=schedule[c]['class'],
            grade=(grades[schedule[c]['class']]['average'] + '%') if grades[schedule[c]['class']]['average'] else None,
            teacher=grades[schedule[c]['class']]['teacher'],
            teacher_email=grades[schedule[c]['class']]['teacher-email'],
            assignments='\n'.join(['<li>{} <span class="assignment-details">{}</span></li>'.format(
                title,
                'Assigned {} - Due {}<br>{}'.format(assignments[title]['assigned'], assignments[title]['due'], assignments[title]['desc'])
            ) for title in assignments.keys() if assignments[title]['class'] == schedule[c]['class']])
        ) for c in schedule.keys() if c not in ('Lunch', 'Ha\'ashara', 'Ma\'amad', 'Chavaya')])


        self.response.attach_file('/accounts/bb_test.html', cache=False,
                                  classes=classes,
                                  menu=escape('\n'.join(updates.SAGEMENU.get(scrape.todaystr(), ('There is no food.',)))).replace('\n', '<br>'))


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
