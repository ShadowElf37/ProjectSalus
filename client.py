user_keys = {

}

whitelist = [

]


class ClientObj:
    def __init__(self, ip, user, login_key=None, admin_key=None):
        self.ip = ip
        self.name = user
        self.logged_in = self.validate(login_key)
        self.admin = self.validate(admin_key)

    def validate(self, s):
        if s is None:
            return False
        return ''.join(map(chr, map(lambda c: ord(c)^97, s))) == user_keys[self.name]