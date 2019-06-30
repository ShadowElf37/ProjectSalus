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
import json
import server.wish as wish
import mail

# REPLACE
TEST = 'Hello World'
TESTTIME = '12:30 pm'
TESTDATE = '05/21/2019'
TESTDT = datetime.strptime(TESTDATE, '%m/%d/%Y')

SCHEDULE_RANGE = (-1, 1)  # Month deltas from current for fetching user schedule span

navbar = get_config('navbar')
from .htmlutil import snippet, ISOWEEKDAYNAMES, ordinal

# Demo

p = info.create_poll('Snack Poll')
p.add_question('Monday', 'Churros', 'Fruit Roll Ups', 'Cereal')
p.add_question('Tuesday', 'Churros1', 'Fruit Roll Ups1', 'Cereal1')
p.add_question('Wednesday', 'Churros2', 'Fruit Roll Ups2', 'Cereal2')
p.add_question('Thursday', 'Churros3', 'Fruit Roll Ups3', 'Cereal3')
p.add_question('Friday', 'Churros4', 'Fruit Roll Ups4', 'Cereal4')

#info.create_announcement('Test', 'This is an announcement.', time()+1000000)
#info.create_announcement('Test 2', 'This is a more recent announcement', time()+1000000)
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
        self.server = self.request.server
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
            email=self.account.email,
            test='hello',
            themeblue='#0052ac',
            themedarkblue='#00429c',
            themeoffwhite='#eeeeee',
            themegrey='#cccccc',
            navbar='\n'.join(['<li{}><a{}>{}</a></li>'.format(' class="active"' if self.path == li[1] else ' class="disabled"' if li[2] else '', (' href="'+li[1]+'"') if not li[2] else '', li[0]) for li in navbar.get(self.rank)]),
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

class HandlerDataRequests(RequestHandler):
    def call(self):
        schedule = self.account.updaters['schedule'].wait()
        grades = self.account.updaters['grades'].wait()
        timespan = [scrape.firstlast_of_month(delta)[i].strftime('%m/%d/%Y') for i,delta in enumerate(SCHEDULE_RANGE)]
        menu = {d:updates.SAGEMENU.get(d) for d in schedule.keys()}
        allergens = updates.SAGEMENUINFO
        if self.account.optimal_poll is None:
            poll = None
        else:
            p = info.POLLS[self.account.optimal_poll]
            poll = p.title, p.id, p.questions

        try:
            self.response.set_body(json.dumps(locals()[self.request.get_query['name'][0]]))
        except Exception as e:
            print(e)
            self.response.set_body('null')


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
        a.email = a.dir.get('email')
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
            account.email = account.dir.get('email')

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
        self.account.bb_enc_pass = encoder.encrypt(self.request.get_post('pass'))
        self.account.bb_auth = auth = self.account.email, self.request.get_post('pass')

        # Log into Blackbaud
        myscraper = scrape.BlackbaudScraper()
        if myscraper.login(*auth).get('t') is None:
            self.response.refuse('Invalid password for %s' % self.account.name)
            self.account.bb_enc_pass = ''
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
            self.response.redirect('/login')
            return

        self.account.optimal_poll = next(filter(lambda p: not p.user_has_responded(self.account), sorted(info.POLLS.values())), type('',(),{'id':None})()).id

        if 'schedule' not in self.account.updaters:
            if self.account.personal_scraper is None:
                self.response.refuse('You must use your Blackbaud password to sign in first.')
                return

            scp: scrape.BlackbaudScraper = self.account.personal_scraper
            auth = self.account.bb_auth
            login_safe = updates.bb_login_safe

            schedule_ps = Poolsafe(login_safe(scp.schedule_span, *auth), self.account.bb_id, start_date=scrape.firstlast_of_month(SCHEDULE_RANGE[0])[0], end_date=scrape.firstlast_of_month(SCHEDULE_RANGE[1])[1])
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
        schedule = schedule.get(TESTDATE, {})

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
        spec = ' / '.join(schedule.get('SPECIAL', [])).lower()
        classday = 'Day {}'.format(scrape.get(schedule, 'DAY', 'of No Class')) + (' (Half Day)' if 'dismissal' in spec else '')
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

        # Generate menu
        menulist = updates.SAGEMENU.get(TESTDATE, ())
        menu = []
        if menulist:
            for item in menulist:
                di = updates.SAGEMENUINFO.get(item, [])
                veg = 'vegitem ' if not any(map(lambda d: d[1] == "Vegetarian", di)) else ''
                menu.append(snippet('menuitem', name=item, veg=veg))

        contains, may_contain, cross = updates.SAGEMENUINFO.get(TESTDATE, ('nothing', 'nothing', ''))

        # Generate announcements
        announcements = [snippet('announcement',
            title=ann.title,
            date=datetime.fromtimestamp(ann.timestamp).strftime('%m/%d/%Y'),
            text='\n'.join(['<p>{}</p>'.format(text) for text in ann.text.split('\n')])
        ) for ann in reversed(info.GENERAL_ANNOUNCEMENTS) if ann.displayed]

        if not announcements:
            announcements = snippet('no-announcement'),

        # Generate assignments
        assignmentlist = []
        for title, assignment in assignments:
            assignmentlist.append(snippet('assignment',
                                          title=title,
                                          due=assignment['due'],
                                          s12='&nbsp;'*12,
                                          assnd=assignment['assigned'],
                                          desc=assignment['desc']))

        # Generate Ma'amad schedule
        maamads = []
        for week in info.MAAMADS:
            if week.is_this_week(TESTDATE):
                for day in week.week:
                    activity, desc = week.get_date(day)
                    dt = datetime.strptime(day, '%m/%d/%Y')
                    maamads.append(snippet('maamad-tab',
                                           title=activity,
                                           desc=desc.replace('\n', '<br>'),
                                           weekday=ISOWEEKDAYNAMES[dt.isoweekday()][:3]+'.',
                                           dayord=ordinal(dt.day)))
                break

        noschool = not periods or 'cancel' in spec or 'close' in spec or 'field day' in spec

        self.response.attach_file('/accounts/landing.html', cache=False,
                                  classday=classday,
                                  next_class_info=snippet('next-class-info-1',
                                                          period=nextclass[0],
                                                          startp=scrape.striptimezeros(nextclass[1]['start']).lower()) if nextclass else 'No school today.' if noschool else 'No more classes today.',
                                  next_class_meta=snippet('next-class-info-2',
                                                           name=nextclass[1]['title'],
                                                           teacher=grades[nextclass[1]['id']]['teacher'],
                                                           email=grades[nextclass[1]['id']]['teacher-email'],
                                                           start=start,
                                                           end=end) if nextclass else snippet('next-class-info-e', msg='Have a lovely day!'),
                                  periods='\n'.join(periods) if periods and not noschool else snippet('no-periods',
                                                                                                      text=(
                                                                                                          'No Classes Today' if not schedule.get('SPECIAL')
                                                                                                              else '<br>'.join(
                                                                                                                  set(schedule['SPECIALFMT'])
                                                                                                              )
                                                                                                          )
                                                                                                      ),
                                  no_school=snippet('red-border') if noschool else '',
                                  announcements='\n'.join(announcements),
                                  allergens=snippet('allergens', contains, may_contain, cross),
                                  prefix=prf['prefix'],
                                  assignments='\n'.join(assignmentlist) if assignmentlist else snippet('no-assignments'),
                                  maamads='\n'.join(maamads) if maamads else snippet('no-maamad'),
                                  menu='\n'.join(menu) if menu else snippet('no-food'))


class HandlerSubmitPoll(RequestHandler):
    def call(self):
        print(self.request.post_vals)

class HandlerConsolePage(RequestHandler):
    def call(self):
        self.response.attach_file('/admin/well.html')

class HandlerConsoleCommand(RequestHandler):
    well = wish.SocketWell([wish.EchoWell, wish.BagelWell, wish.LogWell, wish.SystemWell, wish.DataWell, wish.ReloadWell, wish.PingWell, wish.StatusWell])
    def call(self):
        my_wish = self.request.get_post('command')
        # self.response.fix_buffer(1000)
        self.response.wrest()
        self.well.wish(wish.Wish(my_wish, {
            'server': self.server,
            'response': self.response,
            'outside-world': globals()
        }))


class HandlerDirectory(RequestHandler):
    def call(self):
        self.response.attach_file('/accounts/directory.html', students=updates.DIRECTORY_HTML, teachers=updates.TEACHER_HTML)


class HandlerMailLoginPage(RequestHandler):
    def call(self):
        if self.rank < 1:
            self.response.redirect('/login')
            return
        if self.account.inbox.pwd:
            self.response.redirect('/mail')
            return
        self.response.attach_file('/accounts/mail_login.html')

class HandlerMailLogin(RequestHandler):
    def call(self):
        pwd = self.request.get_post('pass')
        user = self.account.email
        encoder = cryptrix(self.account.password, self.account.name)
        encrypted_pass = encoder.encrypt(pwd)

        session = mail.Inbox(user, pwd, encrypted_pass)
        try:
            session.new_conn()
            session.update(threadpool=updates.updater_pool)
        except mail.imaplib.IMAP4.error:
            self.response.refuse('Incorrect password, or your email stored on Blackbaud is incorrect. If this error occurs outside of testing then Yovel is dumb and tell him immediately.')
            return

        self.account.inbox = session
        self.response.redirect('/mail', get=True)

class HandlerMail(RequestHandler):
    def call(self):
        messages = [msg.body for msg in self.account.inbox.messages]
        self.response.attach_file('/accounts/mail.html', messages='<br><br>'.join(messages))

class HandlerSendMail(RequestHandler):
    def call(self):
        to = self.request.get_post('to')
        body = self.request.get_post('body')

        msg = mail.Message(self.account.email, *to)
        msg.write(body.encode())

        self.response.set_body('Done.')
        try:
            remote = mail.SMTPRemote(self.account.email, self.account.inbox.pwd)
            remote.send(msg)
        except:
            self.response.set_body('An error occurred.', append=False)


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
    '/data': HandlerDataRequests,
    '/well': HandlerConsolePage,
    '/directory': HandlerDirectory,
    '/mail_login': HandlerMailLoginPage,
    '/mail': HandlerMail,
}

POST = {
    '/signup': HandlerSignup,
    '/login': HandlerLogin,
    '/mod-h': HandlerMod,
    '/mod-s': HandlerModServer,
    '/bb_post': HandlerBBLogin,
    '/submit-poll': HandlerSubmitPoll,
    '/wish': HandlerConsoleCommand,
    '/mail_login': HandlerMailLogin,
    '/mail': HandlerSendMail
}

INDEX = {**GET, **POST}
