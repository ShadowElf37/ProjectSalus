import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class FernetS(Fernet):
    def encrypt(self, string):
        return super().encrypt(bytes(string, 'UTF-8'))
    def decrypt(self, token, ttl=None):
        return super().decrypt(token, ttl).decode('UTF-8')

def fernet(key, salt, byte=False):
    if not byte:
        salt = bytes(salt, 'UTF-8')
        key = bytes(key, 'UTF-8')

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend())
    key = base64.urlsafe_b64encode(kdf.derive(key))

    if byte:
        return Fernet(key)
    return FernetS(key)

f = fernet('password', 'ykey-cohen')
f2 = fernet('password', 'ykey-cohen')
token = f.encrypt('helloworld')
token2 = f.encrypt('helloworld')
print(token)
print(token2)
print(f.decrypt(token))
print(f2.decrypt(token2))

import hashlib
def hash(string, salt=''):
    return hashlib.sha512(salt + string).hexdigest()