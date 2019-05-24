from os         import replace, fsync
from os.path    import isfile

class RotationHandler:
    def __init__(self, basename: str, cap: int=-1):
        self.basename = basename
        self.cap = float('inf') if cap < 0 else int(cap)
        try:
            self.handle = open(basename, "r+")
        except FileNotFoundError:
            self.handle = open(basename, "w+")

    def __del__(self):
        self.handle.close()
    
    def resolve_name(self, version: int) -> str:
        return self.basename + ("" if version == 0 else ".{}".format(version))

    def rotate(self) -> None:
        # self.handle.flush()
        # fsync(self.handle.fileno())
        self.handle.close()
        self._rotate(0)
        self.handle = open(self.basename, "w+")

    def _rotate(self, offset: int) -> None:
        src = self.resolve_name(offset)
        offset += 1
        dest = self.resolve_name(offset)
        if isfile(dest) and offset <= self.cap:
            self._rotate(offset)
        replace(src, dest)

    def restore(self, version: int=1) -> None:
        replace(self.resolve_name(version), self.basename)
