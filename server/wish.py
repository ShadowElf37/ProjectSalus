from itertools  import chain
from sys        import stdout
from shlex      import split, quote

class Wish:
    def __init__(self, string, data):
        self.tokens = split(string or '')
        self.location = 0
        self.data = {}
        self.data.update(data)
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
        self.verbage = tuple(k for k in self.lut.keys())
        print(self.lut, self.verbage)
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
    def wish(self, wish):
        self.output(wish, self.BAGEL)

class MultiWell(RecursiveWell):
    QUANTITIES = {
        1: ['one'],
        2: ['couple', 'two', 'pair', 'twain'],
        3: ['three', 'few'],
        4: ['four', 'some']
    }
    LUT = {k: v for (v, l) in QUANTITIES.items() for k in l}
    CAP = 4
    def __init__(self, parent, children):
        super().__init__(parent, children)
        
    def act(self, verb, wish):
        wish.data["count"] = wish.data.get("count", 1)
        if verb in self.LUT:
            number = self.LUT[verb]
            wish.data["count"] *= number
            self.wish(wish)
        if wish.data["count"] > self.CAP:
            self.output(wish, "Too much multiplicity!")
            wish.data["count"] = 0
            return
        ol = wish.location
        for _ in range(wish.data["count"]):
            wish.location = ol
            super().act(verb, wish)

class TTYWell(MultiWell):
    def __init__(self, children):
        super().__init__(self, children)
        self.last = ""
    def output(self, wish, *args):
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
            self.wish(Wish(last + line, {}))

class SocketWell(MultiWell):
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
        wish.data["out"] += "{}{}\n".format(op, data.replace("\n", "\\n"))
    def wish(self, wish):
        wish.data["out"] = ""
        try:
            super().wish(wish)
            wish.tokens = []
            self.input(wish, self.prompt())
        except StopIteration:
            pass
        return wish.data["out"]

if __name__ == "__main__":
    well = TTYWell([EchoWell, BagelWell])
    well.mainloop()
