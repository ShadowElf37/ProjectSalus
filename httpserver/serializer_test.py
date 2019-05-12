from sys import stdout
from serializer import Serializer
from io import StringIO
from time import time

s = Serializer()
f = StringIO()

@s.serializable(None)
class Two1:
    def __init__(self, one):
        self.one = one
    pass

@s.serializable(None, var=2, twos=[])
class One1:
    def __init__(self, var):
        self.var = var
        self.con = 3
        self.twos = [Two1(self) for _ in range(3)]



if __name__ == "__main__":
    print('Timing Alex\'s pile of shit...\n===================================')
    t = time()
    o = One1(5)
    s.register("one1", o)
    s.register("two1", o.twos[0])
    s.commit(f)
    st = f.getvalue()
    print(st)
    del o

    f = StringIO(st)
    s.initialize(f)
    o = s.request('one1')
    print(o)
    print(o.twos)
    