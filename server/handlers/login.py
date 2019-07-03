from .base import *

class HandlerLoginPage(RequestHandler):
    def call(self):
        self.response.attach_file('/accounts/login.html')

class HandlerLogin(RequestHandler):
    def call(self):
        name = self.request.get_post('name')
        password = self.request.get_post('pwd')
        if not (name and password):
            self.response.back()
            return
        pe = hash(password, name)
        self.client.login(name, pe)
        account = self.client.account
        account.password = password
        if self.client.is_real():
            if account.bb_auth == ('', '') and account.bb_enc_pass != '':
                # If the account has cached passwords, load them with the key given
                decoder = cryptrix(account.password, account.name)
                account.bb_auth = decoder.decrypt(account.bb_enc_pass)
            self.response.add_cookie('user_token', account.key, samesite='strict', path='/')
            account.dir = updates.DIRECTORY[account.name]
            account.bb_id = account.dir['id']
            account.email = account.dir.get('email')

            # updates.register_bb_updater(account, 'profile-details', scrape.BlackbaudScraper.dir_details, account.bb_id, )
            # account.updaters['profile'] = updates.register_bb_updater(account, 'profile', scrape.BlackbaudScraper.dir_details, account.bb_id)

            self.response.redirect('/home')
        else:
            self.response.redirect('/login')
