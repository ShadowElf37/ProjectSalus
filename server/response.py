import time
import re
from wsgiref.handlers import format_date_time
from http.cookies import SimpleCookie, Morsel
from .config import get_config
from .cache import guess_mime, CONTENT_TYPE
from fnmatch import fnmatch  # for mime-type matching
from os.path import basename
from http.server import BaseHTTPRequestHandler, HTTPStatus
from urllib.parse import parse_qs
from .htmlutil import *

ENCODING = 'UTF-8'
HTTPCODES = {v: v.phrase for v in HTTPStatus.__members__.values()}
Morsel._reserved['samesite'] = 'SameSite'

cache_db = get_config('cache')


class ByteDict(dict):
    def __getitem__(self, item):
        return self.get(item.decode(ENCODING), 'ERROR').encode(ENCODING)


class Request:
    NONE_COOKIE = object()
    def __init__(self, HTTPRequest: BaseHTTPRequestHandler):
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

        # Search for GET query
        self.get_query = None
        q = self.path.split('?')
        if len(q) > 1:
            self.get_query = parse_qs(q[1])
        self.path = q[0]

        # Generate POST vals
        self.post_vals = None
        if self.type == 'POST':
            content_len = int(self.get_header('content-length'))
            post_body = self.req.rfile.read(content_len)
            self.post_vals = parse_qs(post_body.decode(ENCODING))

        # Generate client object (now done in handlers.py)
        # self.client = client.ClientObj(self.addr[0], self.get_cookie('user_token'))

    def get_header(self, key):
        return self.headers.get(key.lower())

    def get_cookie(self, key):
        v = self.cookie.get(key, Morsel()).value
        return None if v is '_none' else v

    def get_post(self, key):
        v = self.post_vals.get(key)
        if v is None:
            return
        if len(v) == 1:
            v = v[0]
        return v


class Response:
    RENDER = (
        'html',
        'htm',
        'js',
        'css',
        'r',
    )

    def __init__(self, request: Request):
        self.req = request.req
        self.request = request
        self.server = self.req.server
        self.code = 200, 'OK'
        self.header = {}
        self.cookie = SimpleCookie()
        self.body = ''
        self.default_renderopts = ByteDict(
            ip=self.server.host,
            port=self.server.port,
            addr=self.server.host+':'+str(self.server.port),
        )
        self.sent_prematurely = False
        self.head = False
        self.content_type = 'application/octet-stream'
    
    @staticmethod
    def cache_lookup(path, cache_db=cache_db):
        val = cache_db.get('file').get(basename(path), None)
        mimetype = guess_mime(path)
        if val: return val
        for mt in cache_db.get('mime-type'):
            if fnmatch(mimetype, mt['type']):
                return mt['length']
        return cache_db.get('default')

    def set_code(self, n, msg=None):
        self.code = n, msg

    def send_error(self, n, msg=None):
        if msg is None:
            msg = HTTPCODES.get(n)
        self.set_code(n, msg)
        self.set_body('Error ' + str(n) + '\nMessage: '+str(msg))
        self.req.log_error('Client threw %s, %s', n, msg)
        self.add_header('Connection', 'close')

    def no_response(self):
        self.set_code(204)
        self.head = True

    def refuse(self, msg='You do not have permission to view this page.'):
        self.send_error(403, msg)

    def back(self):
        ref = self.request.get_header('referer')
        org = self.request.get_header('origin')
        self.redirect(ref.replace(org, ''))

    def redirect(self, location, permanent=False, get=True):
        self.set_code(303 if get else 307 if not permanent else 308, 'Redirect')
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

    def attach_file(self, path, render=True, resolve_ctype=True, append=False, force_render=False, cache=True, htmlsafe=False, **render_opts):
        """This function has a fair number of very important features to understand.
            Firstly, the path. The path will default to be in /web/, and the cache will automatically search folders from the given path all the way back up to /web/ for a requested file.
            The path here can also accept /../ in order to escape /web/.

            Secondly, rendering. render= will determine whether or not the file will render. force_render= will attempt to render the file even if it's not typically renderable.
            resolve_ctype= will automatically append a Content-Type header by being intelligent.
            cache= will determine whether or not the file should be server-cached (client-caching is defined through cache.cfg)

            Finally, **render_opts decides what, aside from the default_renderopts decided topside, will be rendered with what text."""

        f = self.server.cache.read(path, True, cache=cache)
        if f is None:
            self.send_error(404, 'Requested page not found.')
            return

        # print(path)
        cachelen = Response.cache_lookup(path)
        if cachelen == -1:
            cachelen = '31536000, public'
        self.add_header('Cache-Control', 'max-age={}'.format(cachelen) if cachelen else 'no-store')

        if render and path.split('.')[-1] in Response.RENDER or force_render:
            self.default_renderopts.update(render_opts)
            f = self.render(f, self.default_renderopts)

        mime = guess_mime(path)
        if resolve_ctype:
            self.set_content_type(mime)
        if 'html' in mime or 'xml' in mime or htmlsafe:
            f = f.decode(ENCODING).encode('ascii', 'xmlcharrefreplace')
        self.set_body(f, append=append, ctype=self.content_type)


    @staticmethod
    def render(byte, render_opts):
        f = byte

        defrender = re.findall(b'(#(?:[dD][eE][fF][iI][nN][eE]) +([^ ]*)? +([^;\n\r]*)(?:[;\n\r]*))', f)
        if defrender:
            for df in defrender:
                f.replace(df[1], df[2])

        argrender = set(re.findall(b'\[\[(.[^\]]*)\]\]', f))
        for arg in argrender:
            f = f.replace(b'[[' + arg + b']]', render_opts[arg])
        if defrender:
            for df in defrender:
                f.replace(df[1], df[2])

        kwrender = set(re.findall(b'{{(.[^\}]*)}}', f))
        for kw in kwrender:
            try:
                r = eval(kw)
            except SyntaxError:
                exec(kw)
                r = ''
            except Exception as e:
                f = f.replace(b'{{' + kw + b'}}', e.__class__.__name__.upper().encode(ENCODING))
            if type(r) != bytes:
                r = bytes(str(r), ENCODING)
            f = f.replace(b'{{' + kw + b'}}', r)
        if defrender:
            for df in defrender:
                f.replace(df[1], df[2])
                f.replace(df[0], b'')

        return f

    def set_content_type(self, type):
        self.add_header('Content-Type', type)
        self.content_type = type

    def add_header(self, k, v):
        self.header[k] = v

    def clear_cookie(self, k):
        self.add_cookie(k, Request.NONE_COOKIE)

    def del_cookie(self, k):
        del self.cookie[k]

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

        if type(self.body) is str:
            b = self.body.encode(ENCODING)
        else:
            b = self.body
        self.req.wfile.write(b if b else b'')
