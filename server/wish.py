from functools  import wraps
from itertools  import chain
from sys        import stdout
from shlex      import split, quote

class Wish:
    def __init__(self, string, data):
        self.tokens = split(string or '')
        self.location = 0
        self.data = {}
        self.data.update(data)
        self.last = None
    def consume(self):
        if self.location >= len(self.tokens):
            return None
        rv = self.tokens[self.location]
        self.location += 1
        self.last = rv
        return rv
    def consume_some(self, count):
        return [self.consume() for _ in range(count)]
    def consume_all(self):
        return self.consume_some(len(self.tokens) - self.location)
    def string(self):
        return ' '.join(quote(tok) for tok in self.tokens)

class BasicWell:
    PROMPT      = "What do you wish for?"
    VERBS       = ()
    INVOCATIONS = ("please",)
    IGNORE      = ("a", "an", "of")
    LIST        = "list"
    LISTING     = "You can wish for these things: {}."
    ERROR       = "Wish failed: {}!"
    
    def __init__(self, parent):
        self.parent = parent
    
    def verbs(self):
        return self.VERBS
    def invocations(self):
        return self.INVOCATIONS
    def list(self): # public invocations
        return self.invocations()
    def prompt(self, *args):
        return self.PROMPT.format(*args)

    def wish(self, wish):
        while True:
            verb = wish.consume()
            if verb is None:
                self.input(wish, self.prompt())
                return
            verb = verb.lower()
            if not verb in self.IGNORE:
                break
        if verb == self.LIST:
            self.output(wish, self.LISTING.format(", ".join(self.verbs())))
            wish.tokens = wish.tokens[:wish.location-1]
            self.input(wish, self.prompt())
            return
        value = self.act(verb, wish)
        if value:
            self.output(wish, self.ERROR.format(value))
    def act(self, verb, wish):
        return "No wish implemented"

    def output(self, wish, *args):
        self.parent.output(wish, *args)
    def input(self, wish, prompt):
        self.parent.input(wish, prompt)

class RecursiveWell(BasicWell):
    def __init__(self, parent, children):
        super().__init__(parent)
        self.children = [self.gen_child(child) for child in children]
        self.lut = dict((i, c) for c in self.children for i in c.invocations())
        self.verbage = tuple(i for c in self.children for i in c.list())
    def gen_child(self, child):
        if type(child) is type:
            return child(self)
        return child[0](self, *child[1:])
    def verbs(self):
        return self.verbage
    def act(self, verb, wish):
        if verb not in self.lut:
            return "You can't wish for that!"
        return self.lut[verb].wish(wish)

class EchoWell(BasicWell):
    PROMPT      = "What to echo?"
    INVOCATIONS = ("echo",)
    def act(self, verb, wish):
        self.output(wish, verb, *wish.consume_all())

def argless(cls):
    old_wish = cls.wish
    @wraps(old_wish)
    def wish(self, wish):
        value = self.act(None, wish)
        if value:
            self.output(wish, self.ERROR.format(value))
    cls.wish = wish
    return cls
def multi_well(cap):
    def decor(cls):
        QUANTITIES = {
            1: ['one'],
            2: ['couple', 'two', 'pair', 'twain'],
            3: ['three', 'few'],
            4: ['four', 'some']
        }
        MULTI_LUT = {k: v for (v, l) in QUANTITIES.items() for k in l}
        cls = argless(cls)
        old_act = cls.act
        @wraps(old_act)
        def act(self, _, wish):
            verb = wish.last
            wish.data["count"] = wish.data.get("count", 1)
            if verb in MULTI_LUT:
                number = MULTI_LUT[verb]
                wish.data["count"] *= number
                if wish.consume() is None:
                    self.input(wish, "{} of what?".format(wish.data["count"]))
                    return
                self.wish(wish)
            if wish.data["count"] > cap:
                self.output(wish, "Too much multiplicity!")
                wish.data["count"] = 0
                return
            ol = wish.location
            for _ in range(wish.data["count"]):
                wish.location = ol
                old_act(self, verb, wish)
            wish.data["count"] = 0
        cls.act = act
        old_invocations = cls.invocations
        @wraps(old_invocations)
        def invocations(self):
            return chain(MULTI_LUT.keys(), old_invocations(self))
        cls.invocations = invocations
        cls.list = old_invocations
        return cls
    return decor

@multi_well(4)
class BagelWell(BasicWell):
    INVOCATIONS = ('bagel', 'bagels')
    BAGEL = r"""
    .-"   "-.
  .'   . ;   `.
 /    : . ' :  \
|   `  .-. . '  |
|  :  (   ) ; ` |
|   :  `-'   :  |
 \   .` ;  :   /
  `.   . '   .'
    `-.___.-'"""
    def act(self, _, wish):
        self.output(wish, self.BAGEL)

class TTYWell(RecursiveWell):
    def __init__(self, children):
        super().__init__(self, children)
        self.last = ""
    def output(self, wish, *args):
        print(*args)
    def input(self, wish, prompt):
        print(prompt + " ", end="")
        self.last = wish.string() + " "
        stdout.flush()
        raise StopIteration
    def mainloop(self):
        from sys import stdin
        for line in stdin:
            last = self.last
            self.last = ""
            try:
                wish = Wish(last + line, {})
                self.wish(wish)
                wish.tokens = []
                self.input(wish, self.prompt())
            except StopIteration: pass

class SocketWell(RecursiveWell):
    PROMPT      = "What do you want?"
    def __init__(self, children):
        super().__init__(self, children)
    def output(self, wish, *args):
        self.write("OUT", ' '.join(args), wish)
    def input(self, wish, prompt):
        self.output(wish, prompt + " ")
        self.write("INP", wish.string(), wish)
        raise StopIteration
    @staticmethod
    def write(op, data, wish):
        print(op, data)
        wish.data['wfile'].write("{}{}\n".format(op, data.replace("\n", "\\n")).encode('utf-8'))
        wish.data['wfile'].flush()
    def wish(self, wish):
        try:
            super().wish(wish)
            wish.tokens = []
            self.input(wish, self.prompt())
        except StopIteration:
            pass


class ReloadWell(BasicWell):
    PROMPT      = "Clear config or cache?"
    INVOCATIONS = ("clear",)
    VERBS       = ("config", "cache")
    def act(self, verb, wish):
        server = wish.data['server']
        if verb == 'config':
            server.log('Request to clear config granted.')
            server.reload_config()
            self.output(wish, 'Request to clear config granted.')
        elif verb == 'cache':
            server.log('Request to clear file caches granted.')
            server.reload_cache()
            self.output(wish, 'Request to clear file caches granted.')
        else:
            return 'Invalid clear target %s' % verb

class LogWell(BasicWell):
    INVOCATIONS = ("log",)
    VERBS = ('write', 'read')
    def act(self, verb, wish):
        server = wish.data["server"]
        if verb == 'write':
            server.log(*wish.consume_all(), user='Wishing Well')
            self.output(wish, 'Line written.')
        elif verb == 'read':
            lines = int(wish.consume() or -1)
            server.log('Reading %s lines of log to client.' % lines)
            self.output(wish, server.read_log(lines))
        else:
            self.input(wish, 'What should be done with the log?')

class SystemWell(BasicWell):
    INVOCATIONS = ('system',)
    VERBS = ('reboot', 'update')
    def act(self, verb, wish):
        server = wish.data['server']
        if verb == 'reboot':
            self.output(wish, 'Rebooting, watch out!')
            server.log('Request to reboot granted.')
            server.reboot()
        elif verb == 'update':
            self.output(wish, 'Updating server...')
            server.log('Request to update granted.')
            server.update()
            self.output(wish, 'Update complete!')
        else:
            return 'You can\'t wish for that silly.'

class DataWell(BasicWell):
    INVOCATIONS = ('data',)
    VERBS = ('dump', 'nuke')
    def act(self, verb, wish):
        server = wish.data['server']
        if verb == 'dump':
            target = wish.consume()
            if not target:
                server.SERMANAGER.cleanup()
                server.log('JSON files manually dumped.')
                self.output(wish, 'JSON files manually dumped.')
            else:
                ser = next(filter(lambda s: s.name == target, server.SERMANAGER.serials), None)
                if ser is None:
                    return 'Invalid data dump target %s.' % target
                ser.dump()
                server.log('JSON file %s manually dumped to.' % target)
                self.output(wish, 'JSON file %s manually dumped to.' % target)
        
        elif verb == 'nuke':
            # Add some protections to this to make sure you don't do it accidentally.
            target = wish.consume()
            if target is None:
                self.input(wish, 'Need a nuke target:')
            ser = next(filter(lambda s: s.name == target, server.SERMANAGER.serials), None)
            if ser is None:
                return 'Invalid data nuke target %s.' % target
            ser.nuke()
            self.output(wish, 'Target nuked. Ladies and gentlement, we got \'em.')

        else:
            return 'Invalid data command.'

if __name__ == "__main__":
    well = TTYWell([EchoWell, BagelWell])
    well.mainloop()
