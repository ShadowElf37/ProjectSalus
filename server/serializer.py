from enum       import Enum
from threading  import RLock
from uuid       import uuid4
from functools  import wraps
from importlib  import import_module
from sys        import stderr
from copy       import deepcopy
from .rotate    import RotationHandler
import json
#from config import get_config
localconf = {"dir": "data/", "ref_prefix": "REF##"}; get_config = lambda x: localconf

config = get_config("serializer")

class Dummy:
    pass
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

@can_serialize(lambda val: type(val) is bytes, "_serialize_bytes", "_is_bytes", lambda val: bytes.fromhex(val["data"]))
@can_serialize("_is_primitive", noop2, "_is_primitive", noop2)
class PrimitiveSerializer(BaseSerializer):
    PRIMITIVE_TYPES = (str, int, float, bool, type(None))
    def _is_primitive(self, obj):
        """Checks primitivity-- direct serialization for these"""
        return type(obj) in self.__class__.PRIMITIVE_TYPES
    def _is_bytes(self, obj):
        return self.is_wrapped(obj) and obj["type"] == "bytes"
    def _serialize_bytes(self, obj):
        return self.wrapped("bytes", obj.hex())

@can_serialize("_is_siterable", "_serialize_iterable", "_is_diterable", "_deserialize_iterable")
@can_serialize(lambda val: type(val) is dict, "_serialize_dict", "_is_dict", "_deserialize_dict")
class RecursiveSerializer(PrimitiveSerializer):
    ITERABLE_TYPES  = (list, set, tuple)
    def _is_siterable(self, obj):
        return type(obj) in self.__class__.ITERABLE_TYPES
    def _serialize_iterable(self, obj):
        return {"type": type(obj).__name__, "data":
            [self._serialize(i) for i in iterable]}
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
    def __init__(self):
        self.names = dict()
        self.antipool = dict() # map uuid to serialized data
        self.anticache = set()
        self.pool = dict() # map uuid to name
        self.pool_queue = None
        self.pool_lock = RLock()

    def load(self, file):
        """Read serialized data from a file."""
        stuff = json.load(file)
        self.names.update(stuff["names"])
        self.antipool.update(stuff["pool"])
        self.antiset = set() # everyone out
    
    def get(self, name):
        """Deserialize an object by its name."""
        return self._deserialize(self.names[name])

    def dump(self, file):
        """Dump the objects to be serialized to a file."""
        pool = dict()
        
        for (k, v) in self._pool_iterator():
            pool[k] = v._serialize(self)
        json.dump({"names": self.names, "pool": pool}, file, indent=4)
    
    def set(self, name, obj):
        """Mark an object for serialization"""
        self.names[name] = self._serialize(obj)

    @staticmethod
    def serialized(**kwargs):
        """Register a class as serialiable, calling postinst after deserialization"""
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
        obj = Dummy()
        obj.__class__ = cls
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

    def getfile(self, path):
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
