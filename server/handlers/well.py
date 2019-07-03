from .base import *

class HandlerConsolePage(RequestHandler):
    def call(self):
        self.response.attach_file('/admin/well.html')

class HandlerConsoleCommand(RequestHandler):
    well = wish.SocketWell([wish.EchoWell, wish.BagelWell, wish.LogWell, wish.SystemWell, wish.DataWell, wish.ReloadWell, wish.PingWell, wish.StatusWell])
    def call(self):
        my_wish = self.request.get_post('command')
        # self.response.fix_buffer(1000)
        self.response.wrest()
        self.well.wish(wish.Wish(my_wish, {
            'server': self.server,
            'response': self.response,
            'outside-world': globals()
        }))
