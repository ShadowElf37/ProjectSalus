from wsgiref.handlers import format_date_time
from time import time
from secrets import token_urlsafe
from server.config import get_config
from server.persistent import PersistentDict

user_tokens = PersistentDict('accounts')

whitelist = get_config('whitelist').get('users')

class Account:
    def __init__(self, name, password, key, email=""):
        self.ips = []
        self.name = name
        self.email = email
        self.password = password
        self.last_activity = format_date_time(time())
        self.rank = 1
        self.key = key

    def register_self(self):
        k = ClientObj.new_key()
        user_tokens.set(k, self)
        self.key = k

    def new_key(self):
        user_tokens.delete(self.key)
        self.register_self()
        return self.key

    def check_pwd(self, pwd):
        return self.password == pwd


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
        return self.account

    def login(self, name, password):
        self.account = user_tokens.find(lambda a: a.name.lower() == name.lower() and a.password == password)
        if self.account:
            self.account.register_self()
        return self.account

    def validate_account(self):
        return self.account is not None

#try:
#    user_keys = pickle.load(open('data/accounts.dat', 'rb'))
#except (EOFError, FileNotFoundError):
#    user_keys = dict()
