from importlib import invalidate_caches as refresh, import_module, reload

class Plugins:
    _modding_table = []

    @staticmethod
    def mod(modulename, as_name=None):
        refresh()
        i = import_module(modulename, 'mods')
        reload(i)
        setattr(__class__, as_name if as_name else modulename, i)
        __class__._modding_table.append(i)
        return i

    @staticmethod
    def get_by_name(name):
        return getattr(__class__, name)
    @staticmethod
    def reload_all():
        for module in __class__._modding_table:
            reload(module)
