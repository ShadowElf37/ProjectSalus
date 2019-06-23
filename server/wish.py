from itertools  import chain
from sys        import stdout
from shlex      import split, quote

class Wish:
    def __init__(self, string, ident):
        self.tokens = split(string or '')
        self.location = 0
        self.ident = ident
        self.data = None
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
    LISTING     = "You can wish for these things: {}."
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
        self.verbage = tuple(self.lut.keys())
        print(self.lut)
        print(self.verbage)
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
            self.wish(Wish(last + line, None))

class BagelWell(BasicWell):
    PROMPT = "How many bagels would you like?"
    INVOCATIONS = ('bagel', 'a bagel')
    def act(self, verb, wish):
        self.output(wish, '{} bagel{}, order up.'.format(('one' if verb in ('a', 'an') else verb).title(), 's' if verb not in ('one', 'a', 'an') else ''), *wish.consume_all())

class SocketWell(RecursiveWell):
    PROMPT      = "What do you want?"
    def __init__(self, children):
        super().__init__(self, children)
    def output(self, wish, *args):
        self.write("OUT", ' '.join(args), wish)
    def input(self, wish, prompt):
        self.output(wish, prompt + " ")
        self.write("INP", wish.string(), wish)
    @staticmethod
    def write(op, data, wish):
        wish.data += "{}{}\n".format(op, data)
    def wish(self, wish):
        wish.data = ""
        super().wish(wish)
        wish.tokens = []
        self.input(wish, self.prompt())
        return wish.data

if __name__ == "__main__":
    well = TTYWell([EchoWell])
    well.mainloop()
