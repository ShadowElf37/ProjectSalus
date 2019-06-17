from enum       import Enum
from threading  import RLock
from uuid       import uuid4
from functools  import wraps
from importlib  import import_module
from copy       import deepcopy
from .rotate    import RotationHandler
from inspect    import isfunction, isclass, ismethod
import json
#from config import get_config
localconf = {"dir": "data/", "ref_prefix": "REF##"}; get_config = lambda x: localconf

config = get_config("serializer")

def noop(*args, **kwargs):
    pass
def noop2(self, arg):
    return arg

class Priority(Enum):
    BEFORE  = lambda queue, item: queue.insert(0, item)
    AFTER   = lambda queue, item: queue.append(item)
class BaseSerializer:
    _serializes = []
    _deserializes = []
    def __init__(self):
        self.values = {}

    def load(self, fh):
        self._unpack(json.load(fh))
    
    def dump(self, fh):
        json.dump(self._prepare(), fh, indent=4)
    
    def set(self, name, value):
        self.values[name] = self._serialize(value)
    
    def get(self, name):
        return self._deserialize(self.values[name])

    def _unpack(self, obj):
        """Unpack data loaded from json.load."""
        self.values.update(obj)
    def _prepare(self):
        """Get a object to pass to json.dump."""
        return self.values

    def _serialize(self, obj):
        for (pred, func) in self.__class__._serializes:
            if pred(self, obj):
                return func(self, obj)
        raise TypeError("Attempting to _serialize non-serializable thing {}".format(obj))
    def _deserialize(self, obj):
        for (pred, func) in self.__class__._deserializes:
            if pred(self, obj):
                return func(self, obj)
        raise TypeError("Unsupported deserialization for {}!".format(obj))
    @staticmethod
    def wrap(type, data):
        return {"type": type, "data": data}
    @staticmethod
    def is_wrapped(wrapped):
        return type(wrapped) is dict and "type" in wrapped and "data" in wrapped

def can_serialize(spredicate, serialize, dpredicate, deserialize, priority: Priority=Priority.AFTER):
    def serializer_decor(cls):
        def validate(thing):
            if callable(thing): return thing
            thing = getattr(cls, thing, None)
            if callable(thing): return thing
            raise TypeError("Not a callable or method of the current class!")
        if not issubclass(cls, BaseSerializer):
            raise TypeError("Cannot decorate a non-serializer!")
        priority(cls._serializes,   (validate(spredicate), validate(serialize)))
        priority(cls._deserializes, (validate(dpredicate), validate(deserialize)))
        return cls
    return serializer_decor

@can_serialize(lambda s, val: type(val) is bytes, "_serialize_bytes", "_is_bytes", lambda s, val: bytes.fromhex(val["data"]))
@can_serialize(lambda s, val: val is ..., '_serialize_ellipsis', '_is_ellipsis', lambda s, val: ...)
@can_serialize("_is_primitive", noop2, "_is_primitive", noop2)
class PrimitiveSerializer(BaseSerializer):
    PRIMITIVE_TYPES = (str, int, float, bool, type(None))
    def __init__(self):
        super().__init__()

    def _is_primitive(self, obj):
        """Checks primitivity-- direct serialization for these"""
        return type(obj) in self.__class__.PRIMITIVE_TYPES

    def _is_bytes(self, obj):
        return self.is_wrapped(obj) and obj["type"] == "bytes"
    def _serialize_bytes(self, obj):
        return self.wrap("bytes", obj.hex())

    def _is_ellipsis(self, obj):
        return self.is_wrapped(obj) and obj["type"] == 'ellipsis'
    def _serialize_ellipsis(self, obj):
        return self.wrap('ellipsis', 'ellipsis')

from datetime import datetime, date, time
@can_serialize(lambda s, val: isinstance(val, datetime) or isinstance(val, date) or isinstance(val, time), "_serialize_dt", "_is_dt", "_deserialize_dt")
class DatetimeSerializer(PrimitiveSerializer):
    def _is_dt(self, obj):
        return self.is_wrapped(obj) and obj["type"] in ('date', 'time', 'datetime')

    def _serialize_dt(self, obj):
        n = datetime.now()
        if type(obj) is time:
            return self.wrapped('time', datetime.combine(n.date(), obj).timestamp())
        elif type(obj) is date:
            return self.wrapped('date', datetime.combine(obj, n.time()).timestamp())
        return self.wrapped('datetime', obj.timestamp())

    def _deserialize_dt(self, val):
        typ = val['type']
        dt = datetime.fromtimestamp(val['data'])
        if typ == 'time':
            return dt.time()
        elif typ == 'date':
            return dt.date()
        return dt

@can_serialize(lambda s, f: isfunction(f) or isclass(f) or ismethod(f), '_serialize_func', '_is_func', '_deserialize_func')
class FunctionSerializer(DatetimeSerializer):
    def _is_func(self, obj):
        return self.is_wrapped(obj) and obj['type'] == 'callable'
    def _serialize_func(self, f):
        return self.wrap('callable', dict(module=f.__module__, qualifier=f.__qualname__))
    def _deserialize_func(self, val):
        module = val['data']['module']
        qualifier = val['data']['qualifier']
        obj = import_module(module)
        for piece in qualifier.split('.'):
            obj = getattr(obj, piece)
        return obj

@can_serialize("_is_siterable", "_serialize_iterable", "_is_diterable", "_deserialize_iterable")
@can_serialize(lambda s, val: type(val) is dict, "_serialize_dict", "_is_dict", "_deserialize_dict")
class RecursiveSerializer(FunctionSerializer):
    ITERABLE_TYPES  = (list, set, tuple)
    def __init__(self):
        super().__init__()

    def _is_siterable(self, obj):
        return type(obj) in self.__class__.ITERABLE_TYPES
    def _serialize_iterable(self, obj):
        return {"type": type(obj).__name__, "data":
            [self._serialize(i) for i in obj]}
    def _is_diterable(self, obj):
        return self.is_wrapped(obj) and obj["type"] in map(lambda x: x.__name__, self.__class__.ITERABLE_TYPES)
    def _deserialize_iterable(self, obj):
        return __builtins__.get(obj["type"], None)(self._deserialize(i) for i in obj["data"])

    def _serialize_dict(self, obj):
        return {"type": "dict", "data":
            [{"key": self._serialize(k), "value": self._serialize(v)}
                for (k, v) in obj.items()]}
    def _is_dict(self, obj):
        return self.is_wrapped(obj) and obj["type"] == "dict"
    def _deserialize_dict(self, obj):
        return {x["key"]: self._deserialize(x["value"]) for x in obj["data"]}

@can_serialize("_is_sclass", "_from_pool", "_is_dsclass", "_deserialize_class", Priority.BEFORE)
class ClassSerializer(RecursiveSerializer):
    RPF             = config.get("ref_prefix")
    METACLASSES     = {}
    def __init__(self):
        super().__init__()
        self.antipool = dict() # map uuid to serialized data
        self.antiset = set()
        self.pool = dict() # map uuid to name
        self.pool_queue = None
        self.pool_lock = RLock()

    def _unpack(self, stuff):
        super()._unpack(stuff["values"])
        self.antipool.update(stuff["pool"])
        self.antiset = set() # everyone out
    
    def _prepare(self):
        """Dump the objects to be serialized to a file."""
        pool = dict()
        
        for (k, v) in self._pool_iterator():
            pool[k] = v._serialize(self)
        return {"values": super()._prepare(), "pool": pool}

    @staticmethod
    def extends(base=None, **kwargs):
        """For use with objects that inherit builtins"""
        def make(cls):
            if base is not None and (base not in cls.__bases__):
                raise NotImplementedError('Serialized class %s must inherit emulated superclass %s' % (cls, base))
            cls._baseclass = cls.__bases__[0] if base is None else base
            cls._basevalue = cls._baseclass.__new__(cls._baseclass)
            var = '_value_'+cls._baseclass.__name__

            def __postinit__(self):
                if var not in self.__dict__.keys():
                    self.__dict__[var] = deepcopy(cls._basevalue)
                super(cls._baseclass, self.__dict__[var]).__init__()
            cls.__postinit__ = __postinit__
            def _s_value(self, v):
                super(cls._baseclass, v).__init__()
            setattr(cls, var, property(lambda self: cls._baseclass(self), _s_value))
            
            def point(self, v):
                if type(v) not in self.__class__.__bases__:
                    raise TypeError('Class %s cannot emulate uninherited type %s' % (type(self), type(v)))
                super(type(v), v).__init__()
            cls.point = point

            return ClassSerializer.serialized(_value=cls._basevalue, **kwargs)(cls)
        return make

    @staticmethod
    def serialized(**kwargs):
        """Register a class as serialiable"""
        def s_decor(cls):
            kwargs["_uuid"] = None
            cls._defaults = kwargs
            cls.__preinit__ = getattr(cls, "__preinit__", noop)
            cls.__postinit__ = getattr(cls, "__postinit__", noop)
            inner_init = cls.__init__
            @wraps(inner_init)
            def outer_init(self, *args, **kwargs):
                self.__preinit__()
                self._uuid = str(uuid4())
                inner_init(self, *args, **kwargs)
                self.__postinit__()
            cls.__init__ = outer_init
            cls._serialize = lambda obj, ser: ser._serialize_class(obj, cls.__module__)
            return cls
        return s_decor
    
    def _is_sclass(self, thing):
        """Make sure a thing is serializable."""
        return getattr(thing.__class__, "_defaults", None) != None

    def _from_pool(self, obj):
        """Register an object in the pool."""
        with self.pool_lock:
            if obj._uuid not in self.pool:
                self.pool[obj._uuid] = obj
                if self.pool_queue:
                    self.pool_queue.append(obj._uuid)
        return self.__class__.RPF + obj._uuid
    
    def _pool_iterator(self):
        """Return an iterator over the pool"""
        self.pool_queue = list(self.pool)
        i = 0
        while True:
            with self.pool_lock:
                if i >= len(self.pool_queue): break
                key = self.pool_queue[i]
                val = self.pool[key]
            yield (key, val)
            i += 1
    
    def _serialize_class(self, obj, module):
        """Serialize a class object"""
        data = dict()
        cls = obj.__class__
        value = {
            "type": cls.__name__,
            "module": module,
            "data": data
        }

        assert getattr(obj, "_uuid")
        for key in cls._defaults:
            print(obj.__class__, key)
            data[key] = self._serialize(getattr(obj, key))
        return value

    def _is_dsclass(self, obj):
        return type(obj) is str and obj.startswith(self.__class__.RPF)

    def _lookup_class(self, module, name):
        """Turn a module and a name into a class object"""
        return getattr(import_module(module), name)

    def _deserialize_class(self, ref):
        """Deserialize a class object"""
        data = self.antipool[ref[len(self.__class__.RPF):]]
        uuid = data["data"]["_uuid"]
        if uuid in self.antiset:
            return self.pool[uuid]
        cls = self._lookup_class(data["module"], data["type"])

        metaclass = ClassSerializer.METACLASSES.get(cls, None)
        if metaclass is None:
            metaclass = ClassSerializer.METACLASSES[cls] = type(cls.__name__, cls.__mro__, dict(cls.__dict__))
        obj = cls.__new__(metaclass)
        obj.__class__ = cls

        # obj.__dict__ = dict(cls.__dict__)
        assert self._is_sclass(obj)
        # obj = cls()  # Work on signature
        fields = data["data"]
        # obj.__dict__.update({k: self._deserialize(v) for k, v in fields.items()})
        obj.__preinit__()
        obj.__dict__.update({k: self._deserialize(fields[k])
            if k in fields else (v() if callable(v) else deepcopy(v))
                for k, v in cls._defaults.items()})
        obj.__postinit__()
        self.antiset.add(uuid)
        return obj

class BoundSerializer(ClassSerializer):
    def __init__(self, name):
        super().__init__()
        path = "{}/{}".format(config.get("dir"), name)
        self.setfile(path)

    def __del__(self):
        self.fh.close()

    def getfile(self):
        return self.fh
    
    def setfile(self, path):
        try:
            self.fh = open(path, "r+")
        except FileNotFoundError:
            self.fh = open(path, "w+")

    def load(self, *args):
        self.getfile().seek(0)
        super().load(self.getfile())
    
    def dump(self, *args):
        self.getfile().seek(0)
        self.getfile().truncate()
        super().dump(self.getfile())
        self.getfile().flush()

class BoundRotatingSerializer(BoundSerializer):
    def __init__(self, name):
        super().__init__(name)

    def setfile(self, path):
        self.handler = RotationHandler(path)

    def getfile(self):
        return self.handler.handle

class BSManager:
    def __init__(self):
        self.serials = []
    def make_serializer(self, name):
        s = BoundSerializer(name)
        self.serials.append(s)
        return s
    def cleanup(self):
        for s in self.serials:
            s.dump()
