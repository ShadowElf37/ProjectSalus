from .serializer import BSManager

Manager = BSManager()
AccountsSerializer = Manager.make_serializer('accounts.json')

@AccountsSerializer.serialized(value={})
class PersistentDict(dict):
    def __init__(self):
        self.value = {}
        super().__init__(self.value)

    def valuesl(self):
        return list(self.values())
    def itemsl(self):
        return list(self.items())
    def find(self, condition):
        return next(filter(condition, self.values()), None)

@AccountsSerializer.serialized(value=[])
class PersistentList(list):
    def __init__(self):
        self.value = []
        super().__init__(self.value)

    def find(self, condition):
        return next(filter(condition, self.value), None)

@AccountsSerializer.serialized(value=[])
class PersistentList:
    def __init__(self):
        self.value = []
    def append(self, x):
        self.value.append(x)