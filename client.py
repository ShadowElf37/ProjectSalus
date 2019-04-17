from wsgiref.handlers import format_date_time
from time import time
from secrets import token_urlsafe
import pickle

def save_users():
    pickle.dump(user_keys, open('data/accounts.dat', 'wb'))

whitelist = open('conf/whitelist.cfg').read().split('\n')

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
        user_keys[k] = self
        self.key = k

    def new_key(self):
        del user_keys[self.key]
        k = ClientObj.new_key()
        self.key = k
        user_keys[k] = self
        return self.key

class ClientObj:
    def __init__(self, ip, key=None):
        self.ip = ip

        self.account = user_keys.get(key, None)
        if self.account is not None:
            del user_keys[key]
            k = self.new_key()
            self.account.key = k
            user_keys[k] = self.account
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
