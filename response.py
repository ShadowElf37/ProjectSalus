import time
from wsgiref.handlers import format_date_time

ENCODING = 'UTF-8'

def days_to_seconds(x):
    return x*24*60*60

class Request:
    def __init__(self, HTTPRequest):
        self.req = HTTPRequest
        self.path = self.req.path
        self.headers = self.req.headers
        self.server = self.req.server.server
        print(self.headers)

    def get_header(self, key):
        return self.headers.getheaders(key.lower())

    def get_cookie(self, key):
        ...


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

    def __init__(self, HTTPRequest):
        self.req = HTTPRequest
        self.server = self.req.server.server
        self.code = 200
        self.header = {}
        self.cookies = {}
        self.body = ''
        self.default_renderopts = {
            'ip':self.server.ip,
            'port':self.server.port,
            'addr':self.server.ip+str(self.server.port),
        }

    @staticmethod
    def resolve_content_type(path):
        return Response.CONTENT_TYPE.get(path.split('.')[-1], 'text/plain')

    def set_code(self, n):
        self.code = n

    def load_base_header(self, content_type=None, cache_control='public'):
        if content_type is not None:
            self.set_content_type(content_type)
        self.add_header('Cache-Control', cache_control)
        self.add_header('Date', format_date_time(time.time()))
        self.add_header('Accept-Ranges', 'none')
        self.add_header('Server', self.req.server_version)

    def set_body(self, string, append=False):
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

    def add_cookie(self, k, v, expires_in_days=60, *args, **kwargs):
        kwargs['Expires'] = format_date_time(time.time()+days_to_seconds(expires_in_days))
        kwargs.update(dict(tuple(zip(args, [None]*len(args)))))
        self.cookies[k] = (v, kwargs)

    def compile(self):
        self.load_base_header()
        self.req.send_response(self.code)
        for k,v in self.header.items():
            self.req.send_header(k, v)
        for c in [(i[0] + '=' + i[1][0] + '; ' + '; '.join(j[0]+'='+j[1] if j[1] is not None else j[0] for j in i[1][1].items())) for i in self.cookies.items()]:
            self.req.send_header('Set-Cookie', c)
        self.req.wfile.write(self.body.encode(ENCODING))

    def finish(self):
        self.compile()
        self.req.end_headers()
        self.req.wfile.close()