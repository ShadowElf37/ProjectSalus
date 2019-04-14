class ClientObj:
    def __init__(self, ip, admin=False):
        self.ip = ip
        self.logged_in = False
        self.admin = admin