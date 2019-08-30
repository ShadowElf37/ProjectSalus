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
def get_size(start_path='.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size

# This one is a modded version of above, for funsies; ignores newlines
def get_lines_of_code(start_path='.'):
    total_lines = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp) and (os.path.splitext(fp)[1] or 'nope') in '.js .py .html .css':
                print('Counting', fp)
                with open(fp, 'rb') as f:
                    total_lines += len([l for l in f.readlines() if l.strip()])
    return total_lines

if __name__ == "__main__":
    print(get_lines_of_code('..'))