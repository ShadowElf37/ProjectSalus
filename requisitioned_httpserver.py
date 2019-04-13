import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from response import *
from threadpool import *


class Server:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.domain = 'localhost'
        self.server = HTTPServer((host, port), HTTPMacroHandler)
        self.server.server = self
        self.log('Server initialized.')
        self.overlord = Overlord(8)

    def run(self):
        try:
            self.server.serve_forever()
        except (KeyboardInterrupt, SystemExit):
            self.log('Server quit by user.')
            exit(0)
        except Exception as e:
            self.log('An exception occurred:', e)

    def close(self):
        self.server.server_close()
        self.log('Server shut down safely by user.')

    def log(self, *string):
        print(time.strftime('%X'), *string)


class HTTPMacroHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        req = Request(self)
        rsp = Response(self)
        self.server.server.overlord.push(req, rsp)


if __name__ == '__main__':
    s = Server()
    s.run()