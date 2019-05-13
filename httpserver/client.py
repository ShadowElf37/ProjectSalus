from wsgiref.handlers import format_date_time
from time import time
from secrets import token_urlsafe
from httpserver.config import get_config
from httpserver.persistent import PersistentDict, AccountsSerializer
from random import randint
# from httpserver.serial import Serialized, JSONSerializer as JSER

# whitelist = get_config('whitelist').get('users')

@AccountsSerializer.serialized(name='', password='', key='')
class Account:
    def __init__(self, name, password, key, email=""):
        self.ips = []
        self.name = name
        self.email = email
        self.password = password
        self.last_activity = format_date_time(time())
        self.rank = 1
        self.key = key
        self.id = randint(0, 2**64-1)
        self.shell = False

    def register_self(self):
        k = ClientObj.new_key()
        user_tokens.set(k, self)
        self.key = k

    def new_key(self):
        user_tokens.delete(self.key)
        self.register_self()
        return self.key

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

    def new_key(self):
        return
    def check_pwd(self, pwd):
        return
    def register_self(self):
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
            self.renew_account(key)
        # self.name = self.account.name

    @staticmethod
    def new_key():
        return token_urlsafe()

    def renew_account(self, old_key):
        user_tokens.delete(old_key)
        k = self.new_key()
        self.account.key = k
        user_tokens.set(k, self.account)

    def create_account(self, name, password):
        self.account = Account(name, password, self.new_key())
        self.account.register_self()
        return self.account

    def login(self, name, password):
        self.account = user_tokens.find(lambda a: a.name.lower() == name.lower() and a.password == password)
        if self.account is not None:
            self.account.register_self()
        else:
            self.account = ShellAccount()
        return self.account

    def is_real(self):
        return self.account is not None and self.account.is_real()

from json.decoder import JSONDecodeError

try:
    AccountsSerializer.initialize()
    user_tokens = AccountsSerializer.request('accounts')
except (JSONDecodeError, KeyError):
    user_tokens = PersistentDict()
    AccountsSerializer.register('accounts', user_tokens)
# try:
    # user_tokens = next(filter(lambda o: type(o) == PersistentDict, JSER('data/accounts.json').load()))
# except StopIteration:
    # user_tokens = PersistentDict()
