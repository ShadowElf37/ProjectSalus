from wsgiref.handlers import format_date_time
from time import time
from secrets import token_urlsafe as new_key
from server.config import get_config
from server.persistent import PersistentDict, AccountsSerializer
from server.threadpool import RWLockMixin
from random import randint

whitelist = get_config('whitelist').get('users')

@AccountsSerializer.serialized(ips=[], id=0, rank=1, name='', password='', key='', last_activity='', email='', profile={}, bb_auth='', bb_id='')
class Account(RWLockMixin):
    def __preinit__(self):
        super().__init__()
    def __postinit__(self):
        self.shell = False
    def __init__(self, name, password, key, email=""):
        self.ips = []
        self.name = name
        self.email = email
        self.password = password
        self.last_activity = format_date_time(time())
        self.rank = 1
        self.key = key
        self.id = randint(0, 2**64-1)
        self.profile = {}
        self.bb_cache = {}
        self.bb_auth = ('', '')
        self.bb_t = ''
        self.bb_id = ''

    def register(self, key):
        self.key = key
        user_tokens.set(key, self)

    def manual_key(self, key):
        user_tokens.delete(self.key)
        user_tokens.set(key, self)
        self.key = key

    def check_pwd(self, pwd):
        return self.password == pwd

    def is_real(self):
        return True

class ShellAccount:
    def __init__(self, *args):
        self.rank = 0
        self.key = None
        self.id = None
        self.password = ''
        self.name = ''
        self.email = ''
        self.shell = True
        self.profile = {}
        self.bb_cache = {}
        self.bb_auth = ('', '')
        self.bb_t = ''
        self.bb_id = ''

    def new_key(self):
        return
    def check_pwd(self, pwd):
        return
    def register(self, *args):
        return
    def manual_key(self, *args):
        return

    def is_real(self):
        return False


    def __eq__(self, other):
        if other is None:
            return True
        return self == other

class ClientObj:
    def __init__(self, ip, key=None):
        self.ip = ip
        # print('Available accounts:', user_tokens.value)
        self.account = user_tokens.get(key, ShellAccount())
        if self.account.is_real():
            ...#self.renew_account()

    def renew_account(self):
        self.account.manual_key(new_key())

    def create_account(self, name, password):
        key = new_key()
        self.account = Account(name, password, key)
        self.account.register(key)
        return self.account

    def login(self, name, password):
        self.account = user_tokens.find(lambda a: a.name.lower() == name.lower() and a.password == password)
        if self.account is not None:
            self.account.manual_key(new_key())
        else:
            self.account = ShellAccount()
        return self.account

    def is_real(self):
        return self.account is not None and self.account.is_real()

from json.decoder import JSONDecodeError
try:
    AccountsSerializer.load()
    user_tokens = AccountsSerializer.get('accounts')
except (JSONDecodeError, KeyError):
    user_tokens = PersistentDict()
AccountsSerializer.set('accounts', user_tokens)
