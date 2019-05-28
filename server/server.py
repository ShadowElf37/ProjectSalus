import os, sys, socket, random
from traceback      import format_exc
from time           import sleep
from subprocess     import check_output
from http.server    import HTTPServer
from git            import Repo
from .threadpool    import *
from .response      import *
from .persistent    import Manager
from .handlers      import *
from .config        import CONFIG_CACHE
from .cache         import FileCache
from .              import handlers

RESPONSE_QUEUE = []

class Server(HTTPServer):
    def __init__(self, host='0.0.0.0', port=8080, stdout_buffer=None, *args):
        super().__init__((host, port), HTTPMacroHandler, *args)
        self.host = host
        try:
            self.ip = socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            self.ip = self.host
        self.port = port
        self.domain = 'localhost'
        self.log('Server initialized on {}:{}.'.format(self.ip, port))
        self.pool = Pool(8)
        self.config_cache = CONFIG_CACHE
        self.cache = FileCache()
        self.buffer = stdout_buffer
        self.running = True

    def process_request(self, request, client_address):
        self.pool.push((self, request, client_address))

    def serve_forever(self, shutdown_poll_interval=0.5):
        try:
            super().serve_forever(shutdown_poll_interval)
        except Exception as e:
            raise e
        finally:
            self.cache.close()
            self.pool.cleanup()

    def run(self):
        while self.running:
            try:
                self.pool.launch()
                self.serve_forever()
            except (KeyboardInterrupt, SystemExit):
                self.log('Server quit by user.')
                self.close()
                break
            except Exception as e:
                self.log('=*'*50+'Very bad server-level error:\n' + format_exc()+'\n'+'*='*50)
            finally:
                self.cleanup()
        self.cleanup()

    def reboot(self):
        self.close()
        os._exit(37)

    def get_log(self):
        return self.buffer.getvalue() if self.buffer else None

    def reload_config(self):
        self.config_cache.reload()

    def reload_cache(self):
        self.cache.reload()

    def update(self):
        here = os.path.dirname(os.path.abspath(__file__))
        os.environ["GIT_ASKPASS"] = here + "/askpass.py"
        repo = Repo(here + "/..")
        return repo.pull()

    def close(self):
        self.cleanup()
        self.log('Server shut down safely by user.')

    def shutdown(self):
        self.close()
        os._exit(0)

    def cleanup(self):
        if not self.running: return
        self.running = False
        Manager.cleanup()
        self.server_close()

    @staticmethod
    def log(*string):
        print('Server ['+time.strftime('%D %X')+'] -', *string)


class HTTPMacroHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, msg, *subs):
        sys.stderr.write("%s [%s] - %s\n" %
                         (self.address_string(),
                          time.strftime('%D %X'),
                          msg%subs)
                         )

    def make_error(self, e):
        responses = [
                'Well this is embarrassing.',
                'Oopsie!',
                'Oh, uh, you weren\'t supposed to see this...',
                'That\'s not quite what I thought would happen...'
            ]
        print('='*100+'\nA fatal error was caught in handler:\n' + format_exc()+'\n'+'='*100)
        self.send_error(500, (random.choice(responses) + ' ' + str(e)[0].upper() + str(e)[1:]))
        return 0

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        req = Request(self)
        rsp = Response(req)
        RESPONSE_QUEUE.append(rsp)
        try:
            handler = handlers.GET.get(req.path, handlers.DefaultHandler)(req, rsp)
            handler.pre_call()
            handler.call()
            handler.post_call()
            rsp.finish()
        except Exception as e:
            self.make_error(e)

        while not RESPONSE_QUEUE[0] == rsp:
            sleep(0.0001)
        del RESPONSE_QUEUE[0]

    def do_POST(self):
        req = Request(self)
        rsp = Response(req)
        RESPONSE_QUEUE.append(rsp)
        handler = handlers.POST.get(req.path, handlers.DefaultHandler)(req, rsp)
        try:
            handler.pre_call()
            handler.call()
            handler.post_call()
            rsp.finish()
        except Exception as e:
            self.make_error(e)

        while not RESPONSE_QUEUE[0] == rsp:
            sleep(0.0001)
        del RESPONSE_QUEUE[0]


if __name__ == '__main__':
    s = Server()
    s.run()
