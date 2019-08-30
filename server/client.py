from datetime import datetime
from secrets import token_urlsafe as new_key
from .config import get_config
from .persistent import PersistentDict, AccountsSerializer
from .threadpool import RWLockMixin, Promise
from random import randint

whitelist = get_config('whitelist').get('users')


@AccountsSerializer.serialized(ips=[], id=0, rank=1, name='', password_enc='', key='', last_activity='', email='', bb_auth=None, bb_id='', bb_t='', clubs=[], subscriptions=[], inbox=None, phone='', service_provider='')
class Account(RWLockMixin):
    def __preinit__(self):
        super().__init__()
    def __postinit__(self):
        self.shell = False
        self.bb_t = ''
        self.updaters: {str: Promise} = {}
        self.scheduled = {}
        self.dir = {}
        self.personal_scraper = None
        if not getattr(self, 'password', False):
            self.password = ''
        self.optimal_poll = None

    def __init__(self, name, password, key, email=""):
        self.ips = []
        self.name = name
        self.email = email
        self.password = password
        self.password_enc = ''
        self.bb_auth = Credentials()
        self.last_activity = datetime.now().ctime()
        self.rank = 1
        self.key = key
        self.id = randint(0, 2**64-1)
        self.bb_id = ''
        self.subscriptions = []  # For notifications
        self.clubs = []
        self.inbox = None
        self.phone = ''
        self.service_provider = ''
        self.optimal_poll = None

    def register(self, key):
        self.key = key
        user_tokens[key] = self

    def manual_key(self, key):
        del user_tokens[self.key]
        self.register(key)

    def check_pwd(self, pwd):
        return self.password == pwd

    def is_real(self):
        return True
    def has_inbox(self):
        return bool(self.inbox and self.inbox.auth.decrypted)

class ShellAccount:
    def __init__(self, *args):
        self.rank = 0
        self.key = None
        self.id = None
        self.password = ''
        self.password_enc = ''
        self.name = ''
        self.email = ''
        self.shell = True
        self.bb_auth = Credentials()
        self.bb_t = ''
        self.bb_id = ''
        self.updaters: {str: Promise} = {}
        self.scheduled = {}
        self.dir = {}
        self.subscriptions = []
        self.clubs = []
        self.inbox = None
        self.phone = ''
        self.service_provider = ''
        self.personal_scraper = None
        self.optimal_poll = None

    def new_key(self):
        return
    def check_pwd(self, *args):
        return
    def register(self, *args):
        return
    def manual_key(self, *args):
        return

    def is_real(self):
        return False
    def has_inbox(self):
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

    def login(self, name, password_enc):
        self.account = user_tokens.find(lambda a: a.name.lower() == name.lower() and a.password_enc == password_enc)
        if self.account is not None:
            self.account.manual_key(new_key())
        else:
            self.account = ShellAccount()
        return self.account

    def is_real(self):
        return self.account is not None and self.account.is_real()


@AccountsSerializer.serialized(username=None, password_encrypted=None)
class Credentials:
    def __init__(self, username=None, password=None, cryptrix=None):
        self.username = username
        self.password_encrypted = None
        self.password = password
        self.cryptrix = cryptrix
        if password and cryptrix:
            self.take(password, cryptrix)

    def __postinit__(self):
        self.password = getattr(self, 'password', None)
        self.cryptrix = getattr(self, 'cryptrix', None)
        self.tokens = dict()

    @property
    def creds(self):
        return self.username, self.password

    def give(self, cryptrix):
        self.pass_cryptrix(cryptrix)
        self.decrypt()
    def take(self, password, cryptrix=None):
        if cryptrix is not None:
            self.pass_cryptrix(cryptrix)
        self.pass_password(password)
        self.encrypt()
    def dump(self):
        self.password = None
        self.password_encrypted = None
        self.username = None
        self.cryptrix = None

    def pass_cryptrix(self, crypt):
        self.cryptrix = crypt
    def pass_username(self, username):
        self.username = username
    def pass_password(self, password):
        self.password = password

    @property
    def signed_up(self):
        return bool(self.password_encrypted)
    @property
    def decrypted(self):
        return bool(self.password)
    @property
    def waiting(self):
        return bool(self.password_encrypted and not self.password)

    def encrypt(self):
        self.password_encrypted = self.cryptrix.encrypt(self.password)
        print('ENCRYPTED: %s => %s' % (self.password, self.password_encrypted))
    def decrypt(self, ttl=None):
        self.password = self.cryptrix.decrypt(self.password_encrypted, ttl=ttl)
        print('DECRYPTED: %s => %s' % (self.password_encrypted, self.password))


from json.decoder import JSONDecodeError
try:
    AccountsSerializer.load()
    user_tokens: PersistentDict = AccountsSerializer.get('Accounts')
except (JSONDecodeError, KeyError):
    user_tokens = PersistentDict()
AccountsSerializer.set('Accounts', user_tokens)
