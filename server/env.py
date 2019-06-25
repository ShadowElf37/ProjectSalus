from os         import environ
from os.path    import isfile, expanduser
from re         import compile as recomp

class EnvReader:
    PATHS = (".env", "~/.{}.cfg", "/etc/{}.cfg")
    PATTERN = recomp(r"([^\s=]+)\s*=\s*([^=]+)")
    def __new__(self, name):
        assert name
        value = dict()
        for place in EnvReader.PATHS:
            fname = expanduser(place.format(name))
            if isfile(fname):
                with open(fname, "r") as fh:
                    lineno = 1
                    for line in fh:
                        line = line.strip()
                        if line.startswith("#") or line.isspace() or not line:
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

# Stole from SO and needed a place to dump it - sorry Alex
import os
def get_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size
