from response import *
from log import *
from mercury_server import *
from client import *
import time
from threading import Thread
import handlers

log_request = True
log_transactions = False
log_signin = True
log_signup = True
log_request_flags = False

error = ''

def handle(self, conn, addr, request):
    global error

    # Log request
    if log_request or request.file_type in ('html', 'htm', 'act'):
        self.log.log("Request from ", addr[0], ":", [request.method, request.address, request.cookies] + ([request.flags,] if log_request_flags else []) + [request.post_values,])

    # Finds the client by cookie, creates a response to modify later
    response = Response()
    client = ClientObj(addr[0], request.get_cookie('admin_validator') == 'h2q3uy5ghuwe4htrkiujhbwk3')
    request.client = client
    response.admin = client.admin

    # Default render values - these are input automatically to renders
    global host, port
    render_defaults = {'error':error, 'host':publichost, 'port':port}
    response.default_renderopts = render_defaults

    # Pull simpler address from request
    address = '/'.join(request.address).split('-')[0]

    # If the post values are magically empty, that's a problem... happens more than you'd think
    if request.method == "POST" and not request.post_values:
        error = self.throwError(0, 'a', request.get_last_page(), conn, response=response)
        self.log.log(addr[0], '- That thing happened again... sigh.', lvl=Log.ERROR)
        return

    # Generate handler
    request_handler = handlers.INDEX.get(address, handlers.DefaultHandler)(self, conn, addr, request, response)
    # Get output
    response = request_handler.call()

    # Error
    if response is None:
        error = request_handler.response.error
        return

    # Adds an error, sets page cookie (that thing that lets you go back if error), and sends the response off
    error = ''
    if request.address[-1].split('.')[-1] in ('html', 'htm'):
        response.add_cookie('page', '/'.join(request.address))

    self.send(response, conn)
    conn.close()


# TURN DEBUG OFF FOR ALL REAL-WORLD TRIALS OR ANY ERROR WILL CAUSE A CRASH
# USE SHUTDOWN URLs TO TURN OFF

host = '192.168.1.225'
host = '0.0.0.0'
publichost = host
port = 8080
s = Server(host=host, port=port, debug=True, include_debug_level=False)
s.set_request_handler(handle)
s.open()
