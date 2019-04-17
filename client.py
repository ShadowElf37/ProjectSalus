from wsgiref.handlers import format_date_time
from time import time
from secrets import token_urlsafe
import pickle
from config import get_config
from persistent import PersistentDict

user_tokens = PersistentThing('accounts')

whitelist = get_config('whitelist').get('users')

class Account:
    def __init__(self, name, password, key):
        self.ips = []
        self.name = name
        self.password = password
        self.last_activity = format_date_time(time())
        self.admin = False
        self.key = key

    def register_self(self):
        k = ClientObj.new_key()
        user_tokens.set(k, self)
        self.key = k

    def new_key(self):
        user_tokens.delete(self.key)
        register_self()
        return self.key

class ClientObj:
    def __init__(self, ip, key=None):
        self.ip = ip

        self.account = user_tokens.get(key)
        if self.account is not None:
            user_tokens.delete(key)
            k = self.new_key()
            self.account.key = k
            user_tokens.set(k, self.account)
        # self.name = self.account.name

    @staticmethod
    def new_key():
        return token_urlsafe()

    def create_account(self, name, password):
        self.account = Account(name, password, self.new_key())
        self.account.register_self()

    def validate_account(self):
        return self.account is not None

try:
    user_keys = pickle.load(open('data/accounts.dat', 'rb'))
except (EOFError, FileNotFoundError):
    user_keys = dict()
