import time
from wsgiref.handlers import format_date_time
from http.cookies import SimpleCookie, Morsel
from http.server import BaseHTTPRequestHandler
import client

ENCODING = 'UTF-8'

class Request:
    NONE_COOKIE = object()
    def __init__(self, HTTPRequest):
        self.req = HTTPRequest
        self.path = self.req.path
        self.headers = self.req.headers
        self.server = self.req.server.macroserver
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
            print(self.post_vals)

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
    CONTENT_TYPE = {
        'html': 'text/html',
        'htm': 'text/html',
        'css': 'text/css',
        'js': 'application/javascript',
        'txt': 'text/plain',
        'text': 'text/plain',
        'xml': 'text/xml',
        'ttf': 'font/ttf',
        'font': 'font/ttf',
        'mp3': 'audio/mpeg',
        'wav': 'audio/x-wav',
        'ogg': 'audio/ogg',
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'svg': 'image/svg+xml',
        'mp4': 'video/mp4',
        'mov': 'video/quicktime',
        'h265': 'video/h265',
        'h.265': 'video/h265',
        'avi': 'video/h265',
    }

    RENDER = (
        'html',
        'htm',
        'js',
        'css',
    )

    def __init__(self, request: Request):
        self.req = request.req
        self.macroreq = request
        self.server = self.req.server.macroserver
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
        # self.client = self.macroreq.client (now done in handlers.py

    @staticmethod
    def resolve_content_type(path):
        return Response.CONTENT_TYPE.get(path.split('.')[-1], 'text/plain')

    def set_code(self, n, msg=None):
        self.code = n, msg

    def send_error(self, n, msg=None):
        self.req.send_error(n, msg)
        self.sent_prematurely = True

    def redirect(self, location, permanent=False, get=False):
        self.set_code(303 if get else 307 if not permanent else 308)
        self.add_header('Location', location)

    def load_base(self, content_type=None, cache_control='public'):
        if content_type is not None:
            self.set_content_type(content_type)
        # self.add_header('Date', format_date_time(time.time()))
        # self.add_header('Server', self.req.server_version)
        self.add_header('Cache-Control', cache_control)
        self.add_header('Accept-Ranges', 'none')

    def set_body(self, string, append=False, specify_length=False, ctype='text'):
        if specify_length:
            self.add_header('Content-Length', len(string))
        if append:
            self.body += string
        else:
            self.body = string
        self.set_content_type(ctype)

    def attach_file(self, path, render=True, resolve_ctype=True, append=False, force_render=False, cache=True, binary=True, **render_opts):
        if cache:
            f = self.server.cache.read(path, binary)
        else:
            f = open(path, 'rb' if binary else 'r').read()
            if isinstance(f, bytes):
                try:
                    f = f.decode(ENCODING)
                except UnicodeDecodeError:
                    pass
        if render and path.split('.')[-1] in Response.RENDER or force_render:
            render_opts.update(self.default_renderopts)
            for k,v in render_opts.items():
                f = f.replace('[['+k+']]', str(v))
        self.set_body(f, append=append)

        if resolve_ctype:
            self.add_header('Content-Type', self.resolve_content_type(path))

    def set_content_type(self, type):
        self.add_header('Content-Type', Response.CONTENT_TYPE[type])

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
        self.cookie[k] = v
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
        self.req.wfile.write(self.body.encode(ENCODING))
