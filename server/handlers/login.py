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

        account = self.client.account
        account.password = password

        if self.client.is_real():
            decoder = cryptrix(account.password, account.name)
            # If the account has cached passwords, load them with the key given
            if account.bb_auth.waiting:
                account.bb_auth.give(decoder)

                # Log into Blackbaud
                if self.account.personal_scraper is None:
                    print('NO SCRAPER')
                    self.account.personal_scraper = scrape.BlackbaudScraper()
                    print(self.account.personal_scraper)
                    # If we don't already have cached profile details, create a fetcher for it
                    updates.updater_pool.push(
                        Poolsafe(self.account.personal_scraper.login, *account.bb_auth.creds).after(
                            updates.dsetter(
                                self.account.updaters, 'profile',
                                Poolsafe(
                                    updates.dsetter(
                                        updates.PROFILE_DETAILS, self.account.name,
                                        updates.bb_login_safe(self.account.personal_scraper.dir_details, *account.bb_auth.creds)
                                    ), self.account.bb_id
                                ).after(
                                    updates.dsetter(self.account.scheduled, 'profile', Poolsafe(
                                            updates.chronomancer.metakhronos, updates.MONTHLY, updates.Minisafe(self.account.updaters.get, 'profile'), now=True
                                        )
                                    )
                                )
                            )
                        )
                    )

            if account.inbox and account.inbox.auth.waiting:
                account.inbox.auth.give(decoder)

            self.response.add_cookie('user_token', account.key, samesite='strict', path='/')
            account.dir = updates.DIRECTORY[account.name]
            account.bb_id = account.dir['id']
            account.email = account.dir.get('email')

            # updates.register_bb_updater(account, 'profile-details', scrape.BlackbaudScraper.dir_details, account.bb_id, )
            # account.updaters['profile'] = updates.register_bb_updater(account, 'profile', scrape.BlackbaudScraper.dir_details, account.bb_id)

            self.response.redirect('/home')
        else:
            self.response.redirect('/login')
