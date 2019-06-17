from .serializer import BSManager

Manager = BSManager()
AccountsSerializer = Manager.make_serializer('accounts.json')

class PersistentBuiltin(object): pass


@AccountsSerializer.extends(dict)
class PersistentDict(dict):
    def valuesl(self):
        return list(self.values())
    def itemsl(self):
        return list(self.items())
    def find(self, condition):
        return next(filter(condition, self.values()), None)

@AccountsSerializer.extends(list)
class PersistentList(list):
    def find(self, condition):
        return next(filter(condition, self), None)
