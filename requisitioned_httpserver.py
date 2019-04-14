import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from response import *
from threadpool import *
from handlers import *
import os
import sys
from subprocess import check_output, CalledProcessError

class EpicAwesomeServer(HTTPServer):
    def __init__(self, macroserver, *args):
        super().__init__(*args)
        self.macroserver = macroserver

    def process_request(self, request, client_address):
        self.macroserver.overlord.push((self, request, client_address))


class Server:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.domain = 'localhost'
        self.server = EpicAwesomeServer(self, (host, port), HTTPMacroHandler)
        self.log('Server initialized.')
        self.overlord = Overlord(8)

    def run(self):
        try:
            self.overlord.launch()
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
        self.send_response(200, 'OK')
        self.end_headers()

    def do_GET(self):
        req = Request(self)
        rsp = Response(self)
        handler = handlers.GET.get(req.path, handlers.DefaultHandler)(req, rsp)
        try:
            handler.call()
            rsp.finish()
        except Exception as e:
            print('A fatal error occurred:', e, 'line', e.__traceback__.tb_lineno)
            self.send_error(500, str(e) + 'line' + str(e.__traceback__.tb_lineno))

    def do_POST(self):
        req = Request(self)
        rsp = Response(self)
        handler = handlers.POST.get(req.path, handlers.DefaultHandler)(req, rsp)
        try:
            handler.call()
            rsp.finish()
        except Exception as e:
            print('A fatal error occurred:', e, 'line', e.__traceback__.tb_lineno)
            self.send_error(500, str(e)+' (line '+str(e.__traceback__.tb_lineno))


if __name__ == '__main__':
    s = Server()
    s.run()