from itertools  import chain
from sys        import stdout
from shlex      import split, quote

SESSIONS = {}

class Wish:
    def __init__(self, string, ident):
        self.tokens = split(string)
        self.location = 0
        self.ident = ident
    def consume(self):
        if self.location >= len(self.tokens):
            return None
        rv = self.tokens[self.location]
        self.location += 1
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
    LIST        = "list"
    LISTING     = "You can wish for: {}"
    ERROR       = "Wish failed: {}!"
    
    def __init__(self, parent):
        self.parent = parent
    
    def verbs(self):
        return self.VERBS
    def invocations(self):
        return self.INVOCATIONS
    def prompt(self, *args):
        return self.PROMPT.format(*args)

    def wish(self, wish):
        verb = wish.consume()
        if verb is None:
            self.input(wish, self.prompt())
            return
        if verb == self.LIST:
            self.output(wish, self.LISTING.format(", ".join(self.verbs())))
            wish.tokens = wish.tokens[:wish.location]
            return
        value = self.act(verb, wish)
        if value:
            self.output(wish, self.ERROR.format(value))
        return value
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
        self.lut = dict(chain((c.invocations(), c) for c in self.children))
        self.verbage = tuple(self.lut)
    def gen_child(self, child):
        if type(child) is type:
            return child(self)
        return child[0](self, *child[1:])
    def verbs(self):
        print(self.verbage)
        return self.verbage
    def act(self, verb, wish):
        if verb not in self.lut:
            return "Can't wish for that!"
        return self.lut[verb].wish(wish)

class EchoWell(BasicWell):
    PROMPT      = "What to echo?"
    INVOCATIONS = ("echo",)
    def __init__(self, parent):
        super().__init__(parent)
    def act(self, verb, wish):
        self.output(wish, verb, *wish.consume_all())

class TTYWell(RecursiveWell):
    def __init__(self, children):
        super().__init__(self, children)
        self.last = ""
    def output(self, *args):
        print(*args)
    def input(self, wish, prompt):
        print(prompt + " ", end="")
        self.last = wish.string() + " "
        stdout.flush()
    def mainloop(self):
        from sys import stdin
        for line in stdin:
            last = self.last
            self.last = ""
            result = self.wish(Wish(last + line, None))

class SocketWell(RecursiveWell):
    def __init__(self, children):
        super().__init__(self, children)
    def output(self, wish, *args):
        self.write("OUT", ' '.join(args), wish.ident)
    def input(self, wish, prompt):
        self.output(wish, prompt + " ")
        self.write("INP", wish.string(), wish.ident)
        raise StopIteration
    @staticmethod
    def write(op, data, sock):
        sock.send("{}{}\n".format(op, data).encode('utf-8'))
    def wish(self, wish):
        try:
            super().wish(wish)
        except StopIteration:
            try: self.input(wish, self.prompt())
            except StopIteration: pass

if __name__ == "__main__":
    well = TTYWell([EchoWell])
    well.mainloop()
