import json
import sys
from inspect import signature
import importlib

SERIALIZERS = {}

DEBUG = False

def cleanup():
    for ser in SERIALIZERS.values():
        ser.dump()
        ser.close()

class JSONSerializer:
    def __init__(self, f):
        # For ease of r/w - init as None
        self.mode = None
        # File to use - init as None to avoid overwriting old file
        self.f = None
        self.path = f
        # Dict of objects by their uuids, which allows for object sharing between classes
        self.memdict = {}
        # List of all objects for quick serialization access
        self.objects = []
        # Cache of serializations, stored by instance object
        self.ser_cache = {}
        # Dict of default constructors, stored by class object
        self.default_constructors = {}
        self.bigdictcache = {}

    #def __del__(self):
     #   self.dump()

    def _dump(self, obj):
        json.dump(obj, self.f, indent=4)

    def _load(self):
        self.bigdictcache = json.load(self.f)
        return self.bigdictcache

    def close(self):
        self.f.close()

    def openw(self):
        if self.mode == 'w':
            return
        if self.f and not self.f.closed:
            self.close()
        self.mode = 'w'
        self.f = open(self.path, 'w')

    def openr(self):
        if self.mode == 'r':
            return
        if self.f and not self.f.closed:
            self.close()
        self.mode = 'r'
        self.f = open(self.path, 'r')

    def flush(self):
        self.f.flush()

    # Reserialize all objects and store in cache for dumping
    def cache_all(self):
        for obj in self.objects:
            self.ser_cache[id(obj)] = serialize(obj)

    # Serialize all objects that haven't been serialized yet and cache for dumping (e.g., if some objects cached themselves already but others haven't and you need to dump ASAP)
    def cache_missing(self):
        for obj in self.objects:
            if self.ser_cache.get(id(obj)) is None:
                self.ser_cache[id(obj)] = serialize(obj)

    # Load all objects of given type names from the JSON and return a list of loaded objects
    def load(self, *typenames):
        self.openr()
        self.memdict = dict()
        objects = []
        # Load JSON dict
        bigdict = self._load()
        # Loop through the objects of given types, or all of the types
        for objtype in (bigdict.keys() if not typenames else typenames):
            # Loop through every stored object of that type
            for objid in bigdict[objtype].keys():
                # Deserialize and add to objects
                objects.append(self.deserialize(objtype, objid))

        return objects

    # Dump all serialized objects in cache (does call self.cache_missing()) to the file
    def dump(self):
        self.openw()
        # JSON friendly dict to dump
        vals = {}

        # Initial serialization of objects
        self.cache_missing()
        objs = self.ser_cache.values()

        # Find any objects in the given that need further serialization
        to_serialize = any(ser[3] for ser in objs)
        newobjs = []
        # While there are sub-objects to serialize...
        while to_serialize:
            # Loop through all those sub-objects
            for serialization in objs:
                for obj in serialization[3]:
                    # Throw serialized versions of those sub-objects into newobjs[]
                    s = obj._serialize()
                    # Check to make sure we didn't already serialize the object - this will prevent infinite loops when objects cross-reference each other
                    if s[1] not in map(lambda s: s[1], newobjs):
                        newobjs.append(s)
                # Empty the to_serialize list for that object
                serialization[3] = []
            # Append newobjs[] to the master list of objects
            objs = list(objs) + newobjs
            # Check to make sure we don't have to loop again for any newly nested objects hiding in the sub-objects
            to_serialize = any(len(ser[3]) for ser in objs)

        # Put all of the serialized objects into our dict
        for name, mem, dic, _ in objs:
            # Make sure the class type is in the dict
            if name not in vals:
                vals[name] = {}
            # Add object
            vals[name][mem] = dic
        # Write to JSON
            print('Dumping!', vals)
        self._dump(vals)
        self.flush()
        return 0

    def generate_obj(self, string):
        """Generate an object from a module.Class@0x1234 string and the JSON file"""
        val = string[5:]
        ref, mem = val.split('@')
        if mem not in self.memdict:
            # If not, recurse and generate a new one
            return self.deserialize(ref, mem)
        else:
            # If yes, fetch it
            return self.memdict[mem]

    def deserialize(self, objtype, objid=None):
        """Takes module + class name, original mem address, entire JSON file, and args for the constructor of the object"""

        bigdic = self.bigdictcache

        if objid is None:
            obj = objtype
            newobj = obj
            if type(obj) == dict:
                vardict = obj
            else:
                vardict = {'':obj}
                if DEBUG: print('@', vardict)
        else:
            # Split the module from the class name and import it
            *module, name = objtype.split('.')
            module = '.'.join(module)
            # Summon the object class
            if module:
                obj = getattr(importlib.import_module(module), name)
            else:
                obj = eval(objtype, globals(), locals())
            # Summon constructor
            constructor_args = self.default_constructors.get(obj.__class__, ())
            # Figure out how many parameters there are and fill them after you run out of given constructor args
            excess = [p for p in obj.CONSTRUCTOR_ARGS.parameters.values() if
                      p.kind == p.POSITIONAL_OR_KEYWORD and p.default is p.empty]
            params = constructor_args + (None,) * (len(excess) - len(constructor_args))
            # Instantiate object for modification
            newobj = obj(*params)
            # Get the dict of relevant variables from the JSON
            vardict = bigdic[objtype][objid]
        # Dict to contain new objects
        newvardict = dict()

        # Recurse to find any complex objects needing further deserialization
        for k, v in vardict.copy().items():
            if DEBUG: print('here are the kv:', k, v)
            #if not objid:
                #print('@', vardict)
            # Check for objects to deserialize
            if type(v) == str and v[:5] == 'obj__':
                newvardict[k] = self.generate_obj(v)
            elif type(v) == dict:
                if DEBUG: print('dict', k, v)
                newdict = {}
                for key,val in v.items():
                    if type(val) == str and val[:5] == 'obj__':
                        newdict[key] = self.generate_obj(val)
                    elif type(val) == list:
                        if DEBUG: print('found another list', key, val)
                        t = list
                        if 'tup__' in key:
                            key = key[5:]
                            t = tuple
                        elif 'set__' in key:
                            key = key[5:]
                            t = set
                        des = self.deserialize(val)
                        if DEBUG: print('$$$', des)
                        newdict[key] = t(list(des.values())[0])
                        if DEBUG: print(newdict)
                    elif type(val) == dict:
                        if DEBUG: print('found another dict', key, val)
                        des = self.deserialize(val)
                        newdict[key] = des
                    else:
                        if DEBUG: print('defaulted', key, val)
                        newdict[key] = val
                newvardict[k] = newdict
                # print('#', newvardict)
            elif type(v) in (list, tuple, set):
                if DEBUG: print('list', v)

                # Check for tuples and sets to reconvert
                t = list
                if 'tup__' in k:
                    k = k[5:]
                    t = tuple
                elif 'set__' in k:
                    k = k[5:]
                    t = set

                newlist = []
                for item in v:
                    if type(item) == str and item[:5] == 'obj__':
                        newlist.append(self.generate_obj(item))
                    elif type(item) == list:
                        newlist.append(t(self.deserialize(item)))
                    elif type(item) == dict:
                        if DEBUG: print('this is a nested dict')
                        newlist.append(self.deserialize(item))
                    else:
                        newlist.append(item)
                newvardict[k] = t(newlist)
            else:
                newvardict[k] = v

        # Simply update the automatically generated object vars with the ones created in deserialization
        # This should avoid the issue we get with Pickle that prevents changing the class vars post-storing because update()
        #   doesn't require every var to be addressed
        if objid is not None:
            newobj.__dict__.update(vardict)
            newobj.__dict__.update(newvardict)
            self.memdict[objid] = newobj
            return newobj
        else:
            if DEBUG: print('!', newvardict)
            return newvardict


def serialize(obj):
    """Takes any class and returns a list of properties, along with a serialized dict, for JSONSerializer to handle"""
    quickie = False
    if type(obj) in (dict,):
        serial = obj
        quickie = True
    else:
        # Quickly get the instance vars
        serial = {k:v for k,v in obj.__dict__.items() if k not in obj.__class__.__dict__}
        # Get class name of the object
        name = obj.__class__.__name__
    # List of complex objects I still need to serialize once I fetch them from their nests
    to_serialize = []

    newserial = {}
    oldserial = serial.copy()
    # Check for things I still need to serialize
    for var, subobj in serial.items():
        # Check for tuples and sets, as those can't be stored in JSON
        original_var = var
        if type(subobj) == tuple:
            var = 'tup__'+str(var)
            del oldserial[original_var]
        elif type(subobj) == set:
            var = 'set__'+str(var)
            del oldserial[original_var]

        # Check if object is officially serializable
        seriable = getattr(subobj, 'SERIAL', False)
        if not seriable and type(subobj) not in (dict, list, tuple, int, str, float, set, bool, type(None)) and not callable(subobj):
            # Panic if it isn't
            raise TypeError('Variable \'%s\' in %s contains unserializable object %s' % (original_var, obj, subobj))
        elif seriable:
            # Otherwise, begin serializing
            m = subobj.__module__
            m = m+'.' if m != '__main__' else ''
            # Attach module name to the class name and add @memaddr; e.g. 'obj__server.client.Account@0x12345'
            newserial[var] = 'obj__' + m + subobj.__class__.__name__ + '@' + hex(id(subobj))
            # Add it to the things I need to serialize
            to_serialize.append(subobj)

        # And if it's a list? oh boy
        elif type(subobj) in (list, tuple, set):
            # All of the new things we're serializing
            new = []
            # For every item in the list...
            for item in subobj:
                # Is it serializable?
                seriable2 = getattr(item, 'SERIAL', False)
                if not seriable2 and type(item) not in (dict, list, tuple, int, str, float, set, bool, type(None)):
                    # Panic if it isn't
                    raise TypeError('Variable \'%s\' in %s contains unserializable object %s' % (original_var, obj, item))
                # If it's a dict or list just serialize it in recursion
                elif type(item) in (dict, list, tuple, set):
                    # Serialize can only handle dicts and classes, so we have to pass it a nothing in front
                    new.append(serialize({'':item}))
                # Or if it's an object we can get a nice object tag instead of the serialization
                elif seriable2:
                    m = item.__module__
                    m = m + '.' if m != '__main__' else ''
                    # Attach module name to the class name and add @memaddr; e.g. 'obj__server.client.Account@0x12345'
                    new.append('obj__' + m + item.__class__.__name__ + '@' + hex(id(item)))
                    # Add it to the things I need to serialize
                    to_serialize.append(item)
                # And of course literals etc. should be appended directly
                else:
                    new.append(item)

            # Store new list in serial
            newserial[var] = new

        # Cool now if it's a dict
        elif type(subobj) == dict:
            # All the new serialized stuff
            new = {}
            for k,v in subobj.items():
                # Is is serializable?
                seriable3 = getattr(v, 'SERIAL', False)
                if not seriable3 and type(v) not in (dict, list, tuple, int, str, float, set, bool, type(None)):
                    # Panic if it isn't
                    raise TypeError('Variable \'%s\' in %s contains unserializable object %s' % (original_var, obj, v))
                # If it's a dict or list serialize it in recursion
                elif type(v) in (dict, list, tuple, set):
                    new[k] = serialize({k:v})
                # Or if it's an object we can get a nice object tag instead of the serialization
                elif seriable3:
                    m = v.__module__
                    m = m + '.' if m != '__main__' else ''
                    # Attach module name to the class name and add @memaddr; e.g. '_obj server.client.Account@0x12345'
                    new[k] = 'obj__' + m + v.__class__.__name__ + '@' + hex(id(v))
                    # Add it to the things I need to serialize
                    to_serialize.append(v)
                # And of course just stuff literals in there
                else:
                    new[k] = v

            # Store new dictionary in serial
            newserial[var] = new

    # Class name, mem addr, the dict of objects, all the items that will be further serialized in JSONSerializer.dump_objs()
    oldserial.update(newserial)  # This cuts out all of the x/tup__x duplicates - serial itself can't be modified during the loop so we use oldserial and newserial
    print(obj.__module__)
    return [obj.__module__ + '.' + name, hex(id(obj)), oldserial, to_serialize] if not quickie else tuple(oldserial.values())[0]


def serial_del(self):
    # Serialize and give to serializer cache
    manual_cache(self)
    self.SERIALIZER.objects.remove(self)

def manual_cache(self):
    self.SERIALIZER.ser_cache[id(self)] = serialize(self)

def serial_init(self, *args, **kwargs):
    """init that replaces native __init__ so that serialization setup can be done"""

    # Call native init
    self.cls__init__(*args, **kwargs)
    ser = self.SERIALIZER
    # Pass instance to serializer
    ser.objects.append(self)
    ser.ser_cache[id(self)] = None

def Serialized(filename, *constructor_args, module_name=None):
    """Make cls serializable"""
    filename = 'data/' + filename + '.json'
    def decorator(cls):
        # Passes serializable check and stuff
        cls.SERIAL = True
        cls.MODULE_NAME = module_name
        cls.CONSTRUCTOR_ARGS = signature(cls)
        # Set serialize function
        cls._serialize = serialize
        # Give the class a static global serializer
        if filename in SERIALIZERS:
            cls.SERIALIZER = ser = SERIALIZERS[filename]
        else:
            cls.SERIALIZER = ser = SERIALIZERS[filename] = JSONSerializer(filename)
        # Give the serializer default constructor passed in Serial()
        ser.default_constructors[cls.__class__] = constructor_args
        # Manual caching
        cls.serialize = manual_cache
        # Override __del__
        cls.__del__ = serial_del
        # Override __init__ but move the original so it can be called in new init
        cls.cls__init__ = cls.__init__
        cls.__init__ = serial_init
        return cls
    return decorator


if __name__ == '__main__':
    @Serialized('test')
    class DemoA:
        def __init__(self):
            self.demo = 'bigdemo'

    BIGDEMO = DemoA()

    @Serialized('test')
    class Demo:
        def __init__(self, toplevel=True):
            self.a = 5
            self.b = 10
            self.c = (DemoA(), 2, 3)
            self.d = {"a": 2, 1: 'hello', 5:(DemoA(), {1: DemoA(), 2:3}), 'test': {'x': (DemoA(), DemoA()), 'y':DemoA()}}
            self.bigdemo = BIGDEMO
            if toplevel:
                self.demo = Demo(False)

        def func(self):
            return self.a + 5

    d = Demo()
    d.SERIALIZER.dump()
    objs = d.SERIALIZER.load()
    n = next(filter(lambda a: type(a) == Demo, objs))
    print(n.a, n.b, n.c, n.d, n.demo, n.bigdemo)