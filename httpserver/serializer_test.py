from sys import stdout
from serializer import Serializer

s = Serializer(stdout)

@s.serializable(None)
class Two:
    pass

@s.serializable(None, var=2, twos=[])
class One:
    def __init__(self, var):
        self.var = var
        self.con = 3
        self.twos = [Two() for _ in range(3)]


o = One(5)
s.write("one", o)
s.write("two", o.twos[0])
#print(s.dumps(o.two))
s.commit()
