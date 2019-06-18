from .response import Request, Response
from .client import *
from .config import get_config
from .crypt import *
from .threadpool import Poolsafe, Minisafe
from html import escape, unescape
from time import time
import updates
import scrape
import info
import mods.modding as modding

navbar = get_config('navbar')
from .htmlutil import snippet, ISOWEEKDAYNAMES, ordinal

info.create_announcement('Test', 'This is an announcement.', time()+100000)
info.create_announcement('Test 2', 'This is a more recent announcement', time()+100000)
m = info.create_maamad_week('05/20/2019')
m.set_day(0, 'Ma\'amad', 'Presentation by Mr. Barber')
m.set_day(1, 'Chavaya', '''9th Grade: Meet with Mrs. Larkin in Becker Theater
10th Grade: Flex Time
11th Grade: Flex Time''')
m.set_day(2, 'Ma\'amad', 'Meet with Maccabiah teams (meeting locations will be emailed out)')
m.set_day(3, 'Chavaya', 'Flex Time for all grades')
m.set_day(4, 'Maccabiah', '')

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

    def noclient(self):
        self.response.del_cookie('user_token')
        self.account.manual_key(self.token)

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

class HandlerFavicon(RequestHandler):
    def call(self):
        self.response.redirect('http://bbk12e1-cdn.myschoolcdn.com/ftpimages/813/logo/EWS-Circular-Logo--WHITEBG.png')
        # self.response.attach_file('favicon.ico')

class HandlerMod(RequestHandler):
    def call(self):
        modname = self.request.get_post('mod')
        modding.Plugins.load(modname, into_scope=globals(), concede_scope=globals())
class HandlerModServer(RequestHandler):
    def call(self):
        self.server.load_plugin(self.request.get_post('mod'))

class HandlerControlWords(RequestHandler):
    def call(self):
        self.response.set_body('0')
        cmd = self.request.get_post('cmd')
        self.noclient()

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
            myscraper.login(*auth)
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

        TESTTIME = '12:30 pm'
        TESTDATE = '05/21/2019'
        TESTDT = datetime.strptime(TESTDATE, '%m/%d/%Y')

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

            assignments_ps = Poolsafe(login_safe(scp.assignments, *auth), start_date=scrape.last_sunday(TESTDT), end_date=scrape.next_saturday(TESTDT))
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
        #print(scrape.prettify(schedule))
        schedule = schedule[TESTDATE]

        # Spawn some class updaters to fill gaps; these won't matter for this page but we should spawn them for when they're needed
        scp = self.account.personal_scraper
        auth = self.account.bb_auth
        for cls in schedule.values():
            if type(cls) is not dict:
                continue
            if cls['real']:
                cid = cls['id']
                if cid not in updates.CLASSES:
                    # Create class updater
                    cps = Poolsafe(
                        updates.dsetter(updates.CLASSES, cid, updates.bb_login_safe(scp.get_class_info, *auth)), cid)
                    cu = updates.chronomancer.monthly(1, cps, now=True)
                    updates.chronomancer.track(cu, cid)
                    updates.CLASS_UPDATERS[cid] = cps
                    updates.CLASS_UPDATERS['_'+str(cid)] = cu

                    # Create class topics updater
                    updates.CLASS_TOPICS[cid] = {}
                    tps = Poolsafe(
                        updates.dsetter(updates.CLASS_TOPICS, cid, updates.bb_login_safe(scp.topics, *auth)), cid
                    )
                    tu = updates.chronomancer.daily(scrape.dt_from_timestr(TESTTIME), tps, now=True)
                    updates.chronomancer.track(tu, cid)
                    updates.TOPICS_UPDATERS[cid] = tps
                    updates.TOPICS_UPDATERS['_'+str(cid)] = tu


        assignments = self.account.updaters['assignments'].wait()
        grades = self.account.updaters['grades'].wait()
        #print(scrape.prettify(assignments))
        #print(scrape.prettify(grades))
        prf = self.account.updaters['profile'].wait()

        periods = []
        classday = 'Day {}'.format(schedule['DAY'])
        start = None
        end = None
        nextclass = None
        for period, _class in schedule.items():
            if type(_class) is not dict:
                continue

            if _class['real']:
                s = datetime.strptime(_class['start'], '%I:%M %p').time()
                e = datetime.strptime(_class['end'], '%I:%M %p').time()
                n = datetime.strptime('12:30 pm', '%I:%M %p').time()
                if n < s and nextclass is None:
                    start = scrape.striptimezeros(s.strftime('%I:%M'))
                    end = scrape.striptimezeros(e.strftime('%I:%M'))
                    nextclass = period, _class

                periods.append(snippet('classtab', period=period, classname=_class['title']))
            else:
                periods.append(snippet('nullclass', name=period))

        menulist = updates.SAGEMENU.get(TESTDATE, ('There is no food.',))
        avd = scrape.SageScraper.AVOID
        menu = []
        for item in menulist:
            di = updates.SAGEMENUINFO.get(item, [])
            veg = 'vegitem ' if avd['611'] not in di or avd['601'] not in di[1] else ''
            menu.append(snippet('menuitem', name=item, veg=veg))

        allergen_0 = sorted({al[1] for item in menulist for al in updates.SAGEMENUINFO.get(item, []) if al[0] == 0})  # Contains
        allergen_1 = sorted({al[1] for item in menulist for al in updates.SAGEMENUINFO.get(item, []) if al[0] == 1})  # May contain
        allergen_2 = sorted({al[1] for item in menulist for al in updates.SAGEMENUINFO.get(item, []) if al[0] == 2})  # Cross contamination warning
        contains = ', '.join(allergen_0[:-1]) + ', and ' + allergen_0[-1]
        may_contain = ', '.join(allergen_1[:-1]) + ', and ' + allergen_1[-1]
        cross = 'Some food is subject to cross-contamination in oil.' if allergen_2 else ''

        announcements = [snippet('announcement',
            title=ann.title,
            date=datetime.fromtimestamp(ann.timestamp).strftime('%m/%d/%Y'),
            text='\n'.join(['<p>{}</p>'.format(text) for text in ann.text.split('\n')])
        ) for ann in reversed(info.GENERAL_ANNOUNCEMENTS) if ann.displayed]

        if not announcements:
            announcements = snippet('no-announcement'),

        assignmentlist = []
        for title, assignment in assignments:
            assignmentlist.append(snippet('assignment',
                                          title=title,
                                          due=assignment['due'],
                                          s12='&nbsp;'*12,
                                          assnd=assignment['assigned'],
                                          desc=assignment['desc']))

        maamads = []
        for week in info.MAAMADS:
            if week.is_this_week(TESTDATE):
                for day in week.week:
                    activity, desc = week.get_date(day)
                    dt = datetime.strptime(day, '%m/%d/%Y')
                    maamads.append(snippet('maamad-tab',
                                           title=activity,
                                           desc=desc.replace('\n', '<br>'),
                                           weekday=ISOWEEKDAYNAMES[dt.isoweekday()],
                                           dayord=ordinal(dt.day)))
                break

        self.response.attach_file('/accounts/bb_test.html', cache=False,
                                  classday=classday,
                                  start=start,
                                  end=end,
                                  startp=scrape.striptimezeros(nextclass[1]['start']).lower(),
                                  next_period=nextclass[0],
                                  next_name=nextclass[1]['title'],
                                  next_teacher=grades[nextclass[1]['id']]['teacher'],
                                  next_teacher_email=grades[nextclass[1]['id']]['teacher-email'],
                                  periods='\n'.join(periods),
                                  announcements='\n'.join(announcements),
                                  allergens=snippet('allergens', contains, may_contain, cross),
                                  prefix=prf['prefix'],
                                  assignments='\n'.join(assignmentlist) if assignmentlist else "There are no assignments from any class this week.",
                                  maamads='\n'.join(maamads),
                                  menu='\n'.join(menu))


GET = {
    '/': HandlerBlank,
    '/favicon.ico': HandlerFavicon,
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
    '/mod-h': HandlerMod,
    '/mod-s': HandlerModServer,
    '/bb_post': HandlerBBLogin
}

INDEX = {}
INDEX.update(GET)
INDEX.update(POST)
