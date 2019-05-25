import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import hashlib

class FernetS(Fernet):
    def encrypt(self, string):
        return super().encrypt(bytes(string, 'UTF-8'))
    def decrypt(self, token, ttl=None):
        return super().decrypt(token, ttl).decode('UTF-8')

def cryptrix(key, salt='', byte=False):
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

def hash(string, salt=''):
    return hashlib.sha512(bytes(salt + string, 'UTF-8')).hexdigest()


if __name__ == '__main__':
    f = cryptrix('password', 'ykey-cohen')
    f2 = cryptrix('password', 'ykey-cohen')
    token = f.encrypt('helloworld')
    token2 = f.encrypt('helloworld')
    print(token)
    print(token2)
    print(f.decrypt(token))
    print(f2.decrypt(token2))