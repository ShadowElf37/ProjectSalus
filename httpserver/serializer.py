from threading  import RLock
from uuid       import uuid4
from functools  import wraps
from importlib  import import_module
from sys        import stderr
import json
#from config import get_config
localconf = {"dir": ".", "ref_prefix": "REF##"}; get_config = lambda x: localconf

config = get_config("serializer")

class Dummy:
    pass
def noop(*args, **kwargs):
    pass

class Nonce:
    def __init__(self, desc=None):
        self.desc = desc or "{} object".format(self.__class__.__name__)
    __repr__ = lambda self: "{%s}" % (self.desc)

class Serializer:
    PRIMITIVE_TYPES = (str, int, float, bool, type(None))
    ITERABLE_TYPES  = (list, set, tuple)
    def __init__(self):
        self.names = dict()
        self.antipool = dict() # map uuid to serialized data
        self.pool = dict() # map uuid to name
        self.pool_queue = None
        self.pool_lock = RLock()

    def __del__(self):
        pass

    def initialize(self, file):
        """Read serialized data from a file."""
        stuff = json.load(file)
        self.names.update(stuff["names"])
        self.antipool.update(stuff["pool"])
        self.pool = dict() # everyone out
    
    def request(self, name):
        """Deserialize an object by its name."""
        return self._deserialize(self.names[name])

    def commit(self, file):
        """Dump the objects to be serialized to a file."""
        pool = dict()
        
        for (k, v) in self._pool_iterator():
            pool[k] = v._serialize()
        json.dump({"names": self.names, "pool": pool}, file)
    
    def register(self, name, obj):
        """Mark an object for serialization"""
        self.names[name] = self._serialize(obj)

    def serializable(self, postinst, **kwargs):
        """Register a class as serialiable, calling postinst after deserialization"""
        def s_decor(cls):
            cls._serializable = True
            kwargs["_uuid"] = None
            cls._defaults = kwargs
            cls._postinst = postinst or noop
            inner_init = cls.__init__
            @wraps(inner_init)
            def outer_init(self, *args, **kwargs):
                self._uuid = str(uuid4())
                inner_init(self, *args, **kwargs)
            cls.__init__ = outer_init
            cls._serialize = lambda sel: self._serialize_class(sel, cls.__module__)
            return cls
        return s_decor

    def _is_primitive(self, obj):
        """Checks primitivity-- direct serialization for these"""
        return type(obj) in Serializer.PRIMITIVE_TYPES
    
    def _is_sclass(self, thing):
        """Make sure a class is serializable."""
        return getattr(thing, "_serializable", False)

    def _serialize(self, obj):
        """Serialize one thing."""
        if self._is_sclass(obj.__class__):
            return self._from_pool(obj)
        if self._is_primitive(obj): return obj
        if type(obj) in (list, tuple, set):
            return {"type": type(obj).__name__, "data":
                self._serialize_iterable(obj)}
        if type(obj) is dict:
            return {"type": "dict", "data":
                [{"key": self._serialize(k), "value": self._serialize(v)}
                    for (k, v) in obj.items()]}
        raise TypeError("Attempting to _serialize non-serializable thing {}".format(obj))

    def _from_pool(self, obj):
        """Register an object in the pool."""
        with self.pool_lock:
            entry = self.pool.get(obj._uuid, None)
            if not entry:
                self.pool[obj._uuid] = obj
                if self.pool_queue:
                    self.pool_queue.append(obj._uuid)
        return config.get("ref_prefix") + obj._uuid
    
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
    
    def _serialize_iterable(self, iterable):
        """Serialize an iterable object"""
        return [self._serialize(i) for i in iterable]
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
    
    def _deserialize(self, obj):
        """Deserialize one object."""
        rpf = config.get("ref_prefix")
        if type(obj) is str and obj.startswith(rpf):
            return self._deserialize_class(self.antipool[obj[len(rpf):]])
        if self._is_primitive(obj):
            return obj
        if type(obj) is dict:
            dtype = __builtins__.get(obj["type"], None)
            if dtype in Serializer.ITERABLE_TYPES:
                return self._deserialize_iterable(obj["data"], dtype)
            if obj["type"] == "dict":
                rval = dict()
                for x in obj["data"]:
                    rval[x["key"]] = x["value"]
                return rval
        raise TypeError("Unsupported deserialization for {}!".format(obj))
    
    def _lookup_class(self, module, name):
        """Turn a module and a name into a class object"""
        return getattr(import_module(module), name)

    def _deserialize_iterable(self, obj, dtype):
        return dtype(self._deserialize(i) for i in obj)
    def _deserialize_class(self, data):
        """Deserialize a class object"""
        uuid = data["data"]["_uuid"]
        cached = self.pool.get(uuid, None)
        if cached:
            return cached
        cls = self._lookup_class(data["module"], data["type"])
        assert self._is_sclass(cls)
        obj = Dummy()
        obj.__class__ = cls
        fields = data["data"]
        for k, v in cls._defaults.items():
            setattr(obj, k, self._deserialize(fields[k]) if (k in fields) else v)
        obj._postinst()
        return obj
