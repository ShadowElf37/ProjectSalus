from .base import *

class DefaultHandler(RequestHandler):
    def call(self):
        self.response.attach_file(self.path, cache=False)

class DefaultPOSTHandler(RequestHandler):
    def call(self):
        print(self.request.post_vals)
        self.response.set_body('Data received.')

class HandlerBlank(RequestHandler):
    def call(self):
        self.response.redirect('/home')

class HandlerLog(RequestHandler):
    def call(self):
        self.response.set_body(self.server.get_log())

class HandlerFavicon(RequestHandler):
    def call(self):
        self.response.redirect('http://bbk12e1-cdn.myschoolcdn.com/ftpimages/813/logo/EWS-Circular-Logo--WHITEBG.png')
        # self.response.attach_file('favicon.ico')

class HandlerMod(RequestHandler):
    def call(self):
        modname = self.request.get_post('mod')
        modding.Plugins.load(modname, into_scope=globals(), concede_scope=globals())
class HandlerModServer(RequestHandler):
    def call(self):
        self.server.load_plugin(self.request.get_post('mod'))

class HandlerDataRequests(RequestHandler):
    def call(self):
        if 'schedule' in self.account.updaters:
            schedule = self.account.updaters['schedule'].wait()
            grades = self.account.updaters['grades'].wait()
            menu = {d: updates.SAGEMENU.get(d) for d in schedule.keys()}

        timespan = [scrape.firstlast_of_month(delta)[i].strftime('%m/%d/%Y') for i,delta in enumerate(SCHEDULE_RANGE)]
        allergens = updates.SAGEMENUINFO
        email_map = updates.DIR_EMAIL_MAP

        if self.account.optimal_poll is None:
            poll = None
        else:
            p = info.POLLS[self.account.optimal_poll]
            poll = p.title, p.id, p.questions
        try:
            self.response.set_body(json.dumps(locals()[self.request.get_query['name'][0]]))
        except Exception as e:
            print(e)
            self.response.set_body('null')
