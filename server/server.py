import os, sys, socket, random
from traceback      import format_exc
from http.server    import HTTPServer
from git            import Repo
from .threadpool    import *
from .response      import *
from .persistent    import Manager
from .config        import CONFIG_CACHE
from .cache         import FileCache
from .              import load_handlers as handlers
from .handlers      import default as handlers_default
from json           import JSONDecodeError
import time
import mods.modding

RESPONSE_QUEUE = []

ServerDataSerializer = Manager.make_serializer('serverstats.json')

@ServerDataSerializer.serialized(handled=0, ips=set())
class ServerData:
    def __init__(self):
        self.handled = 0
        self.ips = set()

try:
    ServerDataSerializer.load()
    SERVER_DATA = ServerDataSerializer.get('stats')
except (KeyError, JSONDecodeError):
    SERVER_DATA = ServerData()
ServerDataSerializer.set('stats', SERVER_DATA)


class Server(HTTPServer):
    SERMANAGER = Manager
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
        self.pool = ThreadManager()
        self.config_cache = CONFIG_CACHE
        self.cache = FileCache()
        self.buffer = stdout_buffer
        self.running = True

        # Global stats
        self.stats = SERVER_DATA

        # Session stats
        self.REQUESTS_HANDLED = 0
        self.CONNECTION_ERRORS = 0
        self.MISC_ERRORS = 0
        self.SERVER_LEVEL_ERRORS = 0

    # Overloads socketserver.TCPServer.process_request()
    def process_request(self, request, client_address):
        self.pool.push((self, request, client_address))

    def finish_request(self, request, client_address):
        return self.RequestHandlerClass(request, client_address, self)

    def serve_forever(self, shutdown_poll_interval=0.5):
        try:
            super().serve_forever(shutdown_poll_interval)
        except (KeyboardInterrupt, SystemExit):
            self.log('Server quit by user.')
            self.close()
            raise
        except Exception:
            self.log('\n'+'=*'*50+'\nVery bad server-level error:\n' + format_exc()+'\n'+'*='*50)
            self.SERVER_LEVEL_ERRORS += 1

    def run(self):
        self.pool.launch()
        while self.running:
            try:
                self.serve_forever()
            except (KeyboardInterrupt, SystemExit):
                break
        self.cleanup()

    def reboot(self):
        self.close()
        os._exit(37)

    # DEPRECATED - use read_log()
    def get_log(self):
        return self.buffer.getvalue() if self.buffer else None

    def read_log(self, nlines=-1):
        if nlines == -1:
            return self.get_log()
        log = reversed(self.get_log().split('\n'))
        return '\n'.join([i for i in [next(log, '-null-') for _ in range(nlines+1)] if i])

    def reload_config(self):
        self.config_cache.reload()

    def reload_cache(self):
        self.cache.reload()

    def load_plugin(self, name):
        return mods.modding.Plugins.load(name, into_scope=globals(), concede_scope=globals())

    def update(self):
        here = os.path.dirname(os.path.abspath(__file__))
        os.environ["GIT_ASKPASS"] = here + "/askpass.py"
        repo = Repo(here + "/..")
        return repo.remotes.origin.pull()

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
        self.pool.cleanup()
        self.server_close()

    def scope(self):
        return globals()

    @staticmethod
    def log(*string, user='Server'):
        text = user, '['+time.strftime('%D %X')+'] -', *string
        print(*text)
        return ' '.join(text)


class HTTPMacroHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.0'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.server.REQUESTS_HANDLED += 1
        self.server.stats.handled += 1
        self.server.stats.ips.add(self.address_string())

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
            'That\'s not what I thought would happen...',
            'Oh frick.'
            ]
        print('='*100+'\nA fatal error was caught in handler:\n' + format_exc() + '='*100)
        self.send_error(500, (random.choice(responses) + ' {}: {}'.format(e.__class__.__name__, (str(e)[0].upper() + str(e)[1:]) if str(e) else 'META: NO MESSAGE')))
        return 0

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        req = Request(self)
        rsp = Response(req)
        #RESPONSE_QUEUE.append(rsp)
        try:
            handler = handlers.GET.get(req.path, handlers_default.DefaultHandler)(req, rsp)
            handler.pre_call()
            handler.call()
            handler.post_call()
            rsp.finish()
        except Exception as e:
            self.make_error(e)
            self.server.MISC_ERRORS += 1

        #while RESPONSE_QUEUE[0] != rsp:
        #    time.sleep(0.00001)
        #del RESPONSE_QUEUE[0]

    def do_POST(self):
        req = Request(self)
        rsp = Response(req)
        #RESPONSE_QUEUE.append(rsp)
        handler = handlers.POST.get(req.path, handlers_default.DefaultHandler)(req, rsp)
        try:
            handler.pre_call()
            handler.call()
            handler.post_call()
            rsp.finish()
        except Exception as e:
            self.make_error(e)
            self.server.MISC_ERRORS += 1

        #while RESPONSE_QUEUE[0] != rsp:
        #    time.sleep(0.00001)
        #del RESPONSE_QUEUE[0]

if __name__ == '__main__':
    s = Server()
    s.run()
