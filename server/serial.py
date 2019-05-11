import json
from inspect import signature

class JSON:
    def __init__(self):
        self.f = open('test.dat', 'w+')

    def dump(self, obj):
        json.dump(obj, self.f, indent=4)

    def load(self):
        return json.load(self.f)

    def close(self):
        self.f.close()

    def dump_objs(self, *objs):
        vals = {}
        newobjs = []

        to_serialize = any(ser[3] for ser in objs)
        while to_serialize:
            for serialization in objs:
                *_, subobjs = serialization
                for obj in subobjs:
                    newobjs.append(serialize(obj))
                serialization[3] = []
            objs = list(objs) + newobjs
            to_serialize = any(len(ser[3]) for ser in objs)

        for name, mem, dict, _ in objs:
            if name not in vals:
                vals[name] = {}
            vals[name]['__'+mem] = dict
        self.dump(vals)


class Demo:
    SERIAL = True

    def __init__(self, toplevel=True):
        self.a = 5
        self.b = 10
        self.c = (1, 2, 3)
        if toplevel:
            self.demo = Demo(False)

    def func(self):
        return self.a + 5


def serialize(obj):
    serial = obj.__dict__
    name = obj.__class__.__name__
    to_serialize = []


    for var, subobj in serial.items():
        d = subobj.__dir__()
        if type(subobj) == tuple:
            var = 'tup__'+var
        elif type(subobj) == set:
            var = 'set__'+var

        seriable = getattr(subobj, 'SERIAL', False)
        if not seriable and type(subobj) not in [dict, list, tuple, int, str, float, set] and not callable(subobj):
            raise TypeError('Variable \'%s\' in %s contains unserializable object %s' % (var, name, type(subobj)))
        elif seriable:
            serial[var] = ['@'+hex(id(subobj)), subobj.__module__, subobj.__class__.__name__]
            to_serialize.append(subobj)

    return [name, hex(id(obj)), serial, to_serialize]


def deserialize(obj, vardict):
    params = ['' for param in signature(obj) if param.kind == param.POSITIONAL_ONLY]
    newobj = obj(*params)

    # Render vardict
    for k, v in vardict.items():
        if 'tup__' in k:
            vardict[k[5:]] = tuple(v)
        elif 'set__' in k:
            vardict[k[5:]] = set(v)
        elif type(v) == list and v[0][0] == '@':
            module = v[1]
            name = v[2]
            if module == '__main__':
                make = name
            else:
                exec('import '+module)
                make = module+'.'+name
            return deserialize(make)

    newobj.__dict__.update(vardict)
    return newobj




demos = [serialize(Demo()) for i in range(10)]
serializer = JSON()
serializer.dump_objs(*demos)
#test = serializer.load()
# test['Demo']