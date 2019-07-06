from ..response         import Request, Response
from ..client           import *
from ..htmlutil         import snippet, ISOWEEKDAYNAMES, ordinal
from ..config           import get_config
from ..crypt            import cryptrix, hash
from ..threadpool       import Promise
from datetime           import datetime, date, time
import mods.modding     as modding
import server.wish      as wish
import updates
import scrape
import info
import json
import mail


NAVBAR = get_config('navbar')
SCHEDULE_RANGE = (-1, 1)  # Month deltas from current for fetching user schedule span


#===================================
# INIT FOR TESTING
#===================================

TEST = 'Hello World'
TESTTIME = '12:30 pm'
TESTDATE = '05/21/2019'
TESTDT = datetime.strptime(TESTDATE, '%m/%d/%Y')


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

#===================================
# END TEST INIT
#===================================


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
            hasInbox=str(self.account.has_inbox()).lower(),
            meta="""<meta charset="utf-8" name="viewport" content="width=device-width, initial-scale=1.0">""",
            test='hello world',
            themeblue='#0052ac',
            themedarkblue='#00429c',
            themeoffwhite='#eeeeee',
            themegrey='#cccccc',
            navbar='\n'.join(['<li{}><a{}>{}</a></li>'.format(' class="active"' if self.path == li[1] else ' class="disabled"' if li[2] else '', (' href="'+li[1]+'"') if not li[2] else '', li[0]) for li in NAVBAR.get(self.rank)]),
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