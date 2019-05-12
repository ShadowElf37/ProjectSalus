from sys import stdout
from serializer import Serializer
from io import StringIO

s = Serializer()
f = StringIO()

@s.serializable(None)
class Two:
    def __init__(self, one):
        self.one = one
    pass

@s.serializable(None, var=2, twos=[])
class One:
    def __init__(self, var):
        self.var = var
        self.con = 3
        self.twos = [Two(self) for _ in range(3)]


if __name__ == "__main__":
    o = One(5)
    s.register("one", o)
    s.register("two", o.twos[0])
    s.commit(f)
    st = f.getvalue()
    print(st)
    del o

    f = StringIO(st)
    s.initialize(f)
    o = s.request('one')
    print(o)
    print(o.twos)
