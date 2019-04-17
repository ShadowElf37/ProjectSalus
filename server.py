import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from response import *
from threadpool import *
from handlers import *
import os
import sys
from sys import exit
from subprocess import check_output
from cache import FileCache
import client

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
        self.cache = FileCache()
        self.running = True

    def run(self):
        while self.running:
            try:
                self.overlord.launch()
                self.server.serve_forever()
            except (KeyboardInterrupt, SystemExit):
                self.log('Server quit by user.')
                self.close()
                break
            except Exception as e:
                raise e
                # self.log('An exception occurred:', e)

    def reboot(self):
        self.cache.close()
        self.close()
        os._exit(37)

    def update(self):
        return check_output(['git', 'pull'])

    def close(self):
        self.running = False
        self.cache.close()
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
        rsp = Response(req)
        handler = handlers.GET.get(req.path, handlers.DefaultHandler)(req, rsp)
        try:
            handler.call()
            rsp.finish()
        except Exception as e:
            raise e
            print('A fatal error occurred:', e, 'line', e.__traceback__.tb_lineno, e.__traceback__.tb_lasti, e.__traceback__.tb_next.tb_lasti)
            self.send_error(500, str(e) + ' line ' + str(e.__traceback__.tb_lineno))

    def do_POST(self):
        req = Request(self)
        rsp = Response(req)
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
