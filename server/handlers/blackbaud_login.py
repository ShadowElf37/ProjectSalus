from .base import *

class HandlerBBLoginPage(RequestHandler):
    def call(self):
        if self.rank < 1:
            self.response.redirect('/login')
            return
        if self.account.bb_auth == ('', ''):
            self.response.attach_file('/accounts/bb_login.html')
        else:
            self.response.redirect('/myday')

class HandlerBBLogin(RequestHandler):
    def call(self):
        # However, if the account has no cached passwords, cache it now
        if not self.request.get_post('pass'):
            self.response.back()
            return

        # Encrypt the password for storage and store unencrypted in RAM
        encoder = cryptrix(self.account.password, self.account.name)
        self.account.bb_enc_pass = encoder.encrypt(self.request.get_post('pass'))
        self.account.bb_auth = auth = self.account.email, self.request.get_post('pass')

        # Log into Blackbaud
        myscraper = scrape.BlackbaudScraper()
        if myscraper.login(*auth).get('t') is None:
            self.response.refuse('Invalid password for %s' % self.account.name)
            self.account.bb_enc_pass = ''
            self.account.bb_auth = ('', '')
            return

        # If we don't already have cached profile details, create a fetcher for it
        if 'profile' not in self.account.updaters:
            self.account.personal_scraper = myscraper
            self.account.updaters['profile'] = Poolsafe(
                updates.dsetter(
                    updates.PROFILE_DETAILS, self.account.name, updates.bb_login_safe(myscraper.dir_details, *auth)
                ), self.account.bb_id)
            self.account.scheduled['profile'] = updates.chronomancer.metakhronos(updates.MONTHLY, self.account.updaters['profile'], now=True)

        self.response.redirect('/bb')