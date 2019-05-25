from os         import environ
from os.path    import isfile, expanduser
from re         import compile as recomp

class EnvReader:
    PATHS = (".env", "~/.{}.cfg", "/etc/{}.cfg")
    PATTERN = recomp(r"([^\s=])\s*=\s*([^=])")
    def __new__(self, name):
        assert name
        value = dict()
        for place in EnvReader.PATHS:
            fname = expanduser(place.format(name))
            if isfile(fname):
                with open(fname, "r") as fh:
                    lineno = 1
                    for line in fh:
                        if line.startswith("#") or isspace(line) or not line:
                            continue
                        match = EnvReader.PATTERN.match(line)
                        if match is None:
                            raise ValueError("Malformed syntax at line {} in {}".format(lineno, fname))
                        lineno += 1
                        key, val = match.group(1), match.group(2)
                        value[key] = val
                    break
        value.update(environ)
        return value
