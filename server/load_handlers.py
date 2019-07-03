from .config import get_config
from importlib import import_module

tree = get_config('dir')

GET = {}
POST = {}

for rp, handler in tree.get('GET').items():
    path = handler.split('.')
    module, handle = '.'.join(path[:-1]), path[-1]
    try:
        GET[rp] = getattr(import_module('.'+module, package='server.handlers'), handle)
    except AttributeError:
        raise ImportError('Could not find %s in %s' % (handle, module)) from None

for rp, handler in tree.get('POST').items():
    path = handler.split('.')
    module, handle = '.'.join(path[:-1]), path[-1]
    try:
        POST[rp] = getattr(import_module('.'+module, package='server.handlers'), handle)
    except AttributeError:
        raise ImportError('Could not find %s in %s' % (handle, module)) from None

print('Request handlers loaded.')

INDEX = {**GET, **POST}
