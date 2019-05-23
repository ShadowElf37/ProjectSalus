from .config import get_config
import pickle
from .serializer import BSManager

#cfg = get_config('persistent')

Manager = BSManager()
AccountsSerializer = Manager.make_serializer('accounts.json')

@AccountsSerializer.serialized(value={})
class PersistentDict:
    def __init__(self):
        self.value = {}

    def get(self, k, default):
        return self.value.get(k, default)
    def set(self, k, v):
        self.value[k] = v
    def delete(self, k):
        del self.value[k]

    def values(self):
        return self.value.values()
    def items(self):
        return self.value.items()

    def valuesl(self):
        return list(self.values())
    def itemsl(self):
        return list(self.items())

    def find(self, condition):
        try:
            return next(filter(condition, self.values()))
        except StopIteration:
            return None
