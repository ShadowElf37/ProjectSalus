from .serializer import BSManager

Manager = BSManager()
AccountsSerializer = Manager.make_serializer('accounts.json')

class PersistentBuiltin(object): pass


@AccountsSerializer.carefullySerialized()
class PersistentDict(dict): pass


@AccountsSerializer.carefullySerialized()
class PersistentList(list):
    def find(self, condition):
        return next(filter(condition, self), None)
