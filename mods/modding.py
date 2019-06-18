from importlib import invalidate_caches as refresh, import_module, reload

NONCE = object()
def defines(namespace, name):
    return getattr(namespace, name, NONCE) is not NONCE

class AttrDict:
    def __init__(self, sad_class):
        self.cls = sad_class
    def __setitem__(self, k, v):
        setattr(self.cls, k, v)
    def __getitem__(self, k):
        return getattr(self.cls, k)

class Plugins:
    _modding_table = []

    @staticmethod
    def load(modulename, into_scope=None, concede_scope=None, _as=None):
        refresh()
        i = import_module(modulename, 'mods')
        if into_scope is None:
            into_scope=__class__
        if type(into_scope) is dict:
            into_scope[_as if _as else modulename] = i
        else:
            setattr(into_scope, _as if _as else modulename, i)
        __class__._modding_table.append(i)

        if concede_scope is not None and defines(i, '__main__'):
            if concede_scope is True:
                concede_scope = AttrDict(__class__)
            elif type(concede_scope) is not dict:
                concede_scope = concede_scope.__dict__
            i.__main__(concede_scope)

        print('Mod %s installed as %s. __main__ found: %s. ' % (modulename, _as, bool(concede_scope)))
        return i

    @staticmethod
    def get_by_name(name):
        return getattr(__class__, name)
    @staticmethod
    def reload_all():
        for module in __class__._modding_table:
            reload(module)
