import hashlib

def egcd(a, b):
    if a == 0:
        return (b, 0, 1)
    else:
        g, y, x = egcd(b % a, a)
        return (g, x - (b // a) * y, y)

def modinv(a, m):
    g, x, y = egcd(a, m)
    if g != 1:
        raise Exception('modular inverse does not exist')
    else:
        return x % m

M = 2**2203
P1 = M - 1
P2 = modinv(P1, M)

def hashint(n):
    return n * P1 % M

def unhashint(h):
    return h * P2 % M

def keyhash(key):
    i = sum(map(lambda c: ord(c[1])*c[0]^777, enumerate(key)))
    while len(bin(i)) < 2201:
        i += i//64
    while len(bin(i)) > 2201:
        i -= i//64
    return i

def hashstr(s, key):
    key = keyhash(key)
    return [hashint(ord(c) + key * i) for i,c in enumerate(s)]

def unhashints(ints, key):
    key = keyhash(key)
    return ''.join([chr(unhashint(c + key * i)) for i,c in enumerate(ints)])

def permahash(s):
    return hashlib.sha512(s.encode('utf-8')).hexdigest()

# print(hashstr('ykey-cohen', 'password'))