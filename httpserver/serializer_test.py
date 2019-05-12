from sys import stdout
from serializer import Serializer
from io import StringIO
from time import time

alex = Serializer(True)
yovel = Serializer(False)
f = StringIO()

@alex.serializable(None)
class Two1:
    def __init__(self, one):
        self.one = one
    pass

@alex.serializable(None, var=2, twos=[])
class One1:
    def __init__(self, var):
        self.var = var
        self.con = 3
        self.twos = [Two1(self) for _ in range(3)]

@yovel.serializable(None)
class Two2:
    def __init__(self, one):
        self.one = one
    pass

@yovel.serializable(None, var=2, twos=[])
class One2:
    def __init__(self, var):
        self.var = var
        self.con = 3
        self.twos = [Two2(self) for _ in range(3)]


if __name__ == "__main__":
    print('Timing Alex\'s pile of shit...\n===================================')
    t = time()
    o = One1(5)
    alex.register("one1", o)
    alex.register("two1", o.twos[0])
    alex.commit(f)
    st = f.getvalue()
    print(st)
    del o

    f = StringIO(st)
    alex.initialize(f)
    o = alex.request('one1')
    print(o)
    print(o.twos)
    print('===================================\nResult: %d us' % ((time()-t)*1000000))
    print(time(), t)
    f = StringIO()
    t = time()
    print('Now for Yovel\'s drastic improvement...\n===================================')
    t = time()
    o = One2(5)
    yovel.register("one2", o)
    yovel.register("two2", o.twos[0])
    yovel.commit(f)
    st = f.getvalue()
    print(st)
    del o

    f = StringIO(st)
    yovel.initialize(f)
    o = yovel.request('one2')
    print(o)
    print(o.twos)
    print('===================================\nResult: %d us' % ((time()-t)*1000000))
    print(time(), t)