import time
from wsgiref.handlers import format_date_time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler

ENCODING = 'UTF-8'

class Request:
    def __init__(self, HTTPRequest):
        self.req = HTTPRequest
        self.path = self.req.path
        self.headers = self.req.headers
        self.server = self.req.server.macroserver
        self.addr = self.req.client_address
        self.cookie = SimpleCookie()
        c = self.get_header('Cookie')
        if c is not None:
            self.cookie.load(c)
        self.type = self.req.command
        self.post_vals = None
        if self.type == 'POST':
            content_len = int(self.get_header('content-length'))
            post_body = self.req.rfile.read(content_len)
            self.post_vals = post_body

    def get_header(self, key):
        return self.headers[key.lower()]

    def get_cookie(self, key):
        return self.cookie[key].value

    def get_post(self, key):
        return key


class Response:
    CONTENT_TYPE = {
        'html': 'text/html',
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

    def __init__(self, HTTPRequest: BaseHTTPRequestHandler):
        self.req = HTTPRequest
        self.server = self.req.server.macroserver
        self.code = 200
        self.header = {}
        self.cookie = SimpleCookie()
        self.body = ''
        self.default_renderopts = {
            'ip':self.server.host,
            'port':self.server.port,
            'addr':self.server.host+str(self.server.port),
        }

    @staticmethod
    def resolve_content_type(path):
        return Response.CONTENT_TYPE.get(path.split('.')[-1], 'text/plain')

    def set_code(self, n):
        self.code = n

    def load_base_header(self, content_type=None, cache_control='public'):
        if content_type is not None:
            self.set_content_type(content_type)
        # self.add_header('Date', format_date_time(time.time()))
        # self.add_header('Server', self.req.server_version)
        self.add_header('Cache-Control', cache_control)
        self.add_header('Accept-Ranges', 'none')

    def set_body(self, string, append=False, specify_length=False):
        if specify_length:
            self.add_header('Content-Length', len(string))
        if append:
            self.body += string
        else:
            self.body = string
        self.set_content_type('text')

    def attach_file(self, path, render=True, render_opts=dict(), resolve_ctype=True, append=False):
        f = open(path, 'r').read()
        if render:
            render_opts.update(self.default_renderopts)
            for k,v in render_opts.items():
                f = f.replace('[['+k+']]', str(v))
        self.set_body(f, append=append)

        if resolve_ctype:
            self.set_content_type(self.resolve_content_type(path))

    def set_content_type(self, type):
        self.add_header('Content-Type', Response.CONTENT_TYPE[type])

    def add_header(self, k, v):
        self.header[k] = v

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

        self.cookie[k] = v
        kwargs['expires'] = format_date_time(time.time()+expires_in_days*24*60*60)
        for i in args:
            kwargs[i] = True
        for j in kwargs.keys():
            self.cookie[k][j] = kwargs[j]

    def compile_header(self):
        # self.load_base_header()
        self.req.send_response(self.code)
        for k,v in self.header.items():
            self.req.send_header(k, v)
        print('@', self.cookie.output())
        for cookie in self.cookie.output(header='').split('\n'):
            self.req.send_header('Set-Cookie', cookie)
        self.req.end_headers()

    def finish(self):
        self.compile_header()
        self.req.wfile.write(self.body.encode(ENCODING))
        # self.req.wfile.close()