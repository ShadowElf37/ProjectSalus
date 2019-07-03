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

        p_enc = hash(password, name)
        self.client.login(name, p_enc)

        account = self.account = self.client.account
        account.password = password

        if self.client.is_real():
            decoder = cryptrix(account.password, account.name)
            # If the account has cached passwords, load them with the key given
            if account.bb_auth.waiting:
                account.bb_auth.give(decoder)

                # Log into Blackbaud
                if account.personal_scraper is None:
                    account.personal_scraper = scrape.BlackbaudScraper()

                    # If we don't already have cached profile details, create a fetcher for it
                    def fetch_account_details():
                        account.personal_scraper.login(*account.bb_auth.creds)
                        account.updaters['profile'] = Promise(
                            updates.dsetter(
                                updates.PROFILE_DETAILS, self.account.name, updates.bb_login_safe(account.personal_scraper.dir_details, *account.bb_auth.creds)
                            ), self.account.bb_id)
                        account.scheduled['profile'] = updates.chronomancer.metakhronos(updates.MONTHLY, account.updaters['profile'], now=True)
                    updates.updater_pool.pushf(fetch_account_details)

            if account.inbox and account.inbox.auth.waiting:
                account.inbox.auth.give(decoder)

            self.response.add_cookie('user_token', account.key, samesite='strict', path='/')
            account.dir = updates.DIRECTORY[account.name]
            account.bb_id = account.dir['id']
            account.email = account.dir.get('email')

            self.response.redirect('/home')
        else:
            self.response.redirect('/login')
