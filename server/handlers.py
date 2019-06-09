from .response import Request, Response
from .client import *
from .config import get_config
from .crypt import *
from .threadpool import Poolsafe
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
        a.dir = updates.DIRECTORY[a.name]
        a.bb_id = a.dir['id']
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
            account.dir = updates.DIRECTORY[account.name]
            account.bb_id = account.dir['id']

            # updates.register_bb_updater(account, 'profile-details', scrape.BlackbaudScraper.dir_details, account.bb_id, )
            # account.updaters['profile'] = updates.register_bb_updater(account, 'profile', scrape.BlackbaudScraper.dir_details, account.bb_id)

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
        if not self.request.get_post('pass'):
            self.response.back()
            return

        # Encrypt the password for storage and store unencrypted in RAM
        encoder = cryptrix(self.account.password, self.account.name)
        self.account.bb_enc = encoder.encrypt(self.request.get_post('pass'))
        self.account.bb_auth = auth = updates.DIRECTORY[self.account.name].get('email'), self.request.get_post('pass')

        # Log into Blackbaud
        myscraper = scrape.BlackbaudScraper()
        try:
            myscraper.login(*auth, 't')
        except scrape.StatusError:
            self.response.refuse('Invalid password for %s' % self.account.name)
            self.account.bb_enc = ''
            self.account.bb_auth = ('', '')
            return

        # If we don't already have cached profile details, create a fetcher for it
        if 'profile' not in self.account.updaters:
            self.account.personal_scraper = myscraper
            self.account.updaters['profile'] = Poolsafe(
                updates.dsetter(
                    updates.PROFILE_DETAILS, self.account.name, updates.bb_login_safe(myscraper.dir_details, *auth)
                ), self.account.bb_id)
            self.account.scheduled['profile'] = updates.chronomancer.metakhronos(updates.MONTHLY, self.account.updaters['profile'], now=True)

        self.response.redirect('/bb')

class HandlerBBInfo(RequestHandler):
    def call(self):
        if self.rank < 1:
            self.response.refuse('Sign in please.')
            return

        if 'schedule' not in self.account.updaters:
            if self.account.personal_scraper is None:
                self.response.refuse('You must use your Blackbaud password to sign in first.')
                return

            scp: scrape.BlackbaudScraper = self.account.personal_scraper
            auth = self.account.bb_auth
            login_safe = updates.bb_login_safe

            schedule_ps = Poolsafe(login_safe(scp.schedule_span, *auth), self.account.bb_id, start_date=scrape.firstlast_of_month(-1)[0])
            us = updates.chronomancer.metakhronos(120, schedule_ps, now=True)
            self.account.updaters['schedule'] = schedule_ps
            self.account.scheduled['schedule'] = us

            assignments_ps = Poolsafe(login_safe(scp.assignments, *auth))
            ua = updates.chronomancer.metakhronos(60, assignments_ps, now=True)
            self.account.updaters['assignments'] = assignments_ps
            self.account.scheduled['assignments'] = ua

            # For other pages
            grades_ps = Poolsafe(login_safe(scp.grades, *auth), self.account.bb_id)
            ug = updates.chronomancer.metakhronos(60, grades_ps, now=True)
            self.account.updaters['grades'] = grades_ps
            self.account.scheduled['grades'] = ug

            updates.chronomancer.track(us, self.account.name)
            updates.chronomancer.track(ua, self.account.name)
            updates.chronomancer.track(ug, self.account.name)


        schedule = self.account.updaters['schedule'].wait()
        print(scrape.prettify(schedule))
        schedule = schedule['05/30/2019']

        # Spawn some class updaters to fill gaps; these won't matter for this page but we should spawn them for when they're needed
        scp = self.account.personal_scraper
        auth = self.account.bb_auth
        for cls in schedule:
            if cls['real']:
                cid = cls['id']
                if cid not in updates.CLASSES:
                    cps = Poolsafe(
                        updates.dsetter(updates.CLASSES, cid, updates.bb_login_safe(scp.get_class_info, *auth)),
                        cid)
                    cu = updates.chronomancer.monthly(1, cps, now=True)
                    updates.chronomancer.track(cu, cid)
                    updates.CLASS_UPDATERS[cid] = cps
                    updates.CLASS_UPDATERS['s'+str(cid)] = cu

        assignments = self.account.updaters['assignments'].wait()
        grades = self.account.updaters['grades'].wait()
        print(scrape.prettify(schedule))
        #print(scrape.prettify(assignments))
        #print(scrape.prettify(grades))
        prf = self.account.updaters['profile'].wait() if self.account.name not in updates.PROFILE_DETAILS else updates.PROFILE_DETAILS.get(self.account.name)

        # At the moment we have access to profile, schedule, assignments, grades, and basic class info
        # We will only need profile for prefix, the schedule, assignments, and some basic class info

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
            classname=schedule[c]['title'],
            grade=(grades[schedule[c]['title']]['average'] + '%') if grades[schedule[c]['class']]['average'] else None,
            teacher=grades[schedule[c]['title']]['teacher'],
            teacher_email=grades[schedule[c]['title']]['teacher-email'],
            assignments='\n'.join(['<li>{} <span class="assignment-details">{}</span></li>'.format(
                title,
                'Assigned {} - Due {}<br>{}'.format(assignments[title]['assigned'], assignments[title]['due'], assignments[title]['desc'])
            ) for title in assignments.keys() if assignments[title]['class'] == schedule[c]['title']])
        ) for c in schedule.keys() if c not in ('Lunch', 'Ha\'ashara', 'Ma\'amad', 'Chavaya')])


        self.response.attach_file('/accounts/bb_test.html', cache=False,
                                  classes=classes,
                                  prefix=prf['prefix'],
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
