from threading  import RLock
from uuid       import uuid4
from functools  import wraps
from importlib  import import_module
from sys        import stderr
import json
#from config import get_config
localconf = {"dir": "."}; get_config = lambda x: localconf

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
    def __init__(self, name):
        self.todo = dict()
        self.dirty = False
        
        self.lost_found = dict()
        self.lnf_queue = None
        self.lnf_lock = RLock()
        self.seen = Nonce("SEEN")
        
        if type(name) is type(stderr):
            self.file = name
        else:
            fname = "{}/{}.json".format(config.get("dir"), name)
            self.file = open(fname, "w+")
    
    def __del__(self):
        if self.dirty:
            print("WARN: Serializer {} has dirty bit set".format(self), file=stderr)
        self.file.close()

    def commit(self):
        self.dirty = False
        lost_found = dict()
        
        for (k, v) in self.lnf_iterator():
            lost_found[k] = self.serialize(v)
        self.todo["lost+found"] = lost_found
        json.dump(self.todo, self.file)
        del self.todo["lost+found"]
    
    def write(self, name, obj):
        self.todo[name] = self.serialize(obj)
        self.dirty = True
    
    def dumps(self, obj):
        return dumps(self.serialize(obj))

    def serializable(self, postinst, **kwargs):
        """Registers a class as serialiable, calling postinst after deserialization"""
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
            cls.serialize = lambda sel: self.serialize_class(sel, cls.__module__)
            return cls
        return s_decor

    def is_primitive(self, obj):
        """Checks primitivity-- direct serialization for these"""
        return type(obj) in (str, int, float, bool, type(None))
    
    def is_sclass(self, thing):
        """Make sure a classed object is serializable."""
        return getattr(thing.__class__, "_serializable", False)

    def serialize(self, obj):
        """Top-level frontend for serialization"""
        if self.is_sclass(obj): return obj.serialize()
        if self.is_primitive(obj): return obj
        if type(obj) in (list, tuple, set):
            return {"type": type(obj).__name__, "data":
                self.serialize_iterable(obj)}
        if type(obj) is dict:
            return {"type": "dict", "data":
                [{"key": self.serialize_r(k), "value": self.serialize_r(v)}
                    for (k, v) in obj.items()]}
        raise TypeError("Attempting to serialize non-serializable thing {}".format(obj))

    def serialize_r(self, obj):
        """Serialize, but put objects in the lost-n-found"""
        if self.is_sclass(obj):
            return self.lostnfound(obj)
        return self.serialize(obj)

    def lostnfound(self, obj):
        """Register an object in the lost-and-found."""
        with self.lnf_lock:
            entry = self.lost_found.get(obj._uuid, None)
            if not entry:
                self.lost_found[obj._uuid] = obj
                if self.lnf_queue:
                    self.lnf_queue.append(obj._uuid)
        return "REF##" + obj._uuid
    
    def lnf_iterator(self):
        self.lnf_queue = list(self.lost_found)
        i = 0
        while True:
            with self.lnf_lock:
                if i >= len(self.lnf_queue): break
                key = self.lnf_queue[i]
                val = self.lost_found[key]
            if val is not self.seen:
                yield (key, val)
            i += 1
    
    def serialize_iterable(self, iterable):
        """Serialize an iterable object"""
        return [self.serialize_r(i) for i in iterable]
    def serialize_class(self, obj, module):
        """Serialize a class object"""
        with self.lnf_lock:
            cached = self.lost_found.get(obj._uuid, None)
            if cached and cached is not self.seen:
                self.lost_found[obj._uuid] = self.seen
                return cached.serialize()
        data = dict()
        cls = obj.__class__
        value = {
            "type": cls.__name__,
            "module": module,
            "data": data
        }

        assert getattr(obj, "_uuid")
        for key in cls._defaults:
            data[key] = self.serialize_r(getattr(obj, key))
        return value
    
    def lookup_class(self, module, name):
        """Turn a module and a name into a class object"""
        return getattr(module, name) if module == "__main__" else eval(name, globals(), locals())

    def deserialize_class(self, data):
        """Deserialize a class object"""
        cls = self.lookup_class(data["module"], data["type"])
        assert self.is_sclass(cls)
        obj = Dummy()
        obj.__class__ = cls
        fields = data["data"]
        for k, v in cls._defaults:
            setattr(obj, k, fields.get(k, v))
        obj._postinst()
