import time
from wsgiref.handlers import format_date_time
from http.cookies import SimpleCookie, Morsel
from server.config import get_config
from fnmatch import fnmatch  # for mime-type matching
from mimetypes import guess_type  # ditto
from os.path import basename

ENCODING = 'UTF-8'

cache_db = get_config('cache')

class Request:
    NONE_COOKIE = object()
    def __init__(self, HTTPRequest):
        self.req = HTTPRequest
        self.path = self.req.path
        self.headers = self.req.headers
        self.server = self.req.server
        self.addr = self.req.client_address
        self.type = self.req.command
        self.cookie = SimpleCookie()

        # Generate cookies
        c = self.get_header('Cookie')
        if c is not None:
            self.cookie.load(c)

        # Generate POST vals
        self.post_vals = None
        if self.type == 'POST':
            content_len = int(self.get_header('content-length'))
            post_body = self.req.rfile.read(content_len)
            self.post_vals = dict(pair.split('=') for pair in post_body.decode(ENCODING).split('&'))

        # Generate client object (now done in handlers.py)
        # self.client = client.ClientObj(self.addr[0], self.get_cookie('user_token'))

    def get_header(self, key):
        return self.headers.get(key.lower())

    def get_cookie(self, key):
        v = self.cookie.get(key, Morsel()).value
        return None if v is '_none' else v

    def get_post(self, key):
        return self.post_vals.get(key)


class Response:

    RENDER = (
        'html',
        'htm',
        'js',
        'css',
    )

    def __init__(self, request: Request):
        self.req = request.req
        self.macroreq = request
        self.server = self.req.server
        self.code = 200, None
        self.header = {}
        self.cookie = SimpleCookie()
        self.body = ''
        self.default_renderopts = {
            'ip':self.server.host,
            'port':self.server.port,
            'addr':self.server.host+str(self.server.port),
        }
        self.sent_prematurely = False
        self.head = False
        # self.client = self.macroreq.client (now done in handlers.py)
    
    @staticmethod
    def cache_lookup(path, cache_db=cache_db):
        val = cache_db.get('file').get(basename(path), None)
        mimetype = guess_type(path)[0]
        if mimetype is None:
            mimetype = 'text/plain'
        if val: return val
        for mt in cache_db.get('mime-type'):
            if fnmatch(mimetype, mt['type']):
                return mt['length']
        return cache_db.get('default')

    def set_code(self, n, msg=None):
        self.code = n, msg

    def send_error(self, n, msg=None):
        self.req.send_error(n, msg)
        self.sent_prematurely = True

    def redirect(self, location, permanent=False, get=False):
        self.set_code(303 if get else 307 if not permanent else 308)
        self.add_header('Location', location)

    def load_base(self, content_type=None):
        if content_type is not None:
            self.set_content_type(content_type)
        self.add_header('Accept-Ranges', 'none')
        self.add_header('Content-Length', str(len(self.body if self.body is not None else '')))

    def set_body(self, string, append=False, specify_length=False, ctype='text/plain'):
        if specify_length:
            self.add_header('Content-Length', len(string))
        if append:
            self.body += string
        else:
            self.body = string
        self.set_content_type(ctype)

    def attach_file(self, path, render=True, resolve_ctype=True, append=False, force_render=False, cache=True, binary=True, **render_opts):
        """This function has a fair number of very important features to understand.
            Firstly, the path. The path will default to be in /web/, and the cache will automatically search folders from the given path all the way back up to /web/ for a requested file.
            The path here can also accept /../ in order to escape /web/.

            Secondly, rendering. render= will determine whether or not the file will render. force_render= will attempt to render the file even if it's not typically renderable.
            resolve_ctype= will automatically append a Content-Type header by being intelligent.
            cache= will determine whether or not the file should be server-cached (client-caching is defined through cache.cfg)
            binary= will manually decide whether or not the file should be read in binary - this is enabled by default, and the class still handles plain text appropriately.

            Finally, **render_opts decides what, aside from the default_renderopts decided topside, will be rendered with what text."""

        f = self.server.cache.read(path, binary, cache)
        if f == None:
            self.send_error(404)
            return None

        # print(path)
        cachelen = Response.cache_lookup(path)
        if cachelen == -1:
            cachelen = '31536000, public'
        self.add_header('Cache-Control', 'max-age={}'.format(cachelen) if cachelen else 'no-store')

        if render and path.split('.')[-1] in Response.RENDER or force_render:
            render_opts.update(self.default_renderopts)
            for k,v in render_opts.items():
                f = f.replace(b'[['+bytes(str(k), ENCODING)+b']]', bytes(str(v), ENCODING))
        self.set_body(f, append=append)

        if resolve_ctype:
            self.add_header('Content-Type', guess_type(path))

    def set_content_type(self, type):
        self.add_header('Content-Type', type)

    def add_header(self, k, v):
        self.header[k] = v

    def clear_cookie(self, k):
        self.add_cookie(k, Request.NONE_COOKIE)

    def add_cookie(self, k, v, *args, expires_in_days=60, **kwargs):
        """
        Valid args:
            httponly
            secure
        Valid kwargs:
            samesite (strict, lax)
            domain [domain]
            comment [comment]
            max-age [seconds]
            version [version]
        """

        if v is Request.NONE_COOKIE:
            del self.cookie[k]
            return
        self.cookie[k] = v if v is not None else '_none'
        kwargs['expires'] = format_date_time(time.time()+expires_in_days*24*60*60)
        for i in args:
            kwargs[i] = True
        for j in kwargs.keys():
            self.cookie[k][j] = kwargs[j]

    def compile_header(self):
        self.load_base()
        self.req.send_response(*self.code)
        for k,v in self.header.items():
            self.req.send_header(k, v)
        for cookie in self.cookie.output(header='').split('\n'):
            self.req.send_header('Set-Cookie', cookie)
        self.req.end_headers()

    def finish(self):
        if self.sent_prematurely:
            return
        self.compile_header()
        if self.head:
            return

        try:
            b = self.body.encode(ENCODING)
        except AttributeError:
            b = self.body
        self.req.wfile.write(b if b else b'')
