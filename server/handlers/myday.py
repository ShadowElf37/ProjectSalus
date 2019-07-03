from .base import *

class HandlerBBInfo(RequestHandler):
    def call(self):
        if self.rank < 1:
            self.response.redirect('/login')
            return

        self.account.optimal_poll = next(filter(lambda p: not p.user_has_responded(self.account), sorted(info.POLLS.values())), type('',(),{'id':None})()).id

        print('GETTING MYDAY')
        print(self.account.personal_scraper)

        if 'schedule' not in self.account.updaters:
            if self.account.personal_scraper is None:
                self.response.refuse('You must use your Blackbaud password to sign in first.')
                return

            print('SCRAPER IS', self.account.personal_scraper)

            scp: scrape.BlackbaudScraper = self.account.personal_scraper
            auth = self.account.bb_auth.creds
            login_safe = updates.bb_login_safe

            print('SCRAPING...')

            schedule_ps = Poolsafe(login_safe(scp.schedule_span, *auth), self.account.bb_id, start_date=scrape.firstlast_of_month(SCHEDULE_RANGE[0])[0], end_date=scrape.firstlast_of_month(SCHEDULE_RANGE[1])[1])
            us = updates.chronomancer.metakhronos(120, schedule_ps, now=True)
            self.account.updaters['schedule'] = schedule_ps
            self.account.scheduled['schedule'] = us

            assignments_ps = Poolsafe(login_safe(scp.assignments, *auth), start_date=scrape.last_sunday(TESTDT), end_date=scrape.next_saturday(TESTDT))
            ua = updates.chronomancer.metakhronos(60, assignments_ps, now=True)
            self.account.updaters['assignments'] = assignments_ps
            self.account.scheduled['assignments'] = ua

            # For other pages
            grades_ps = Poolsafe(login_safe(scp.grades, *auth), self.account.bb_id)
            ug = updates.chronomancer.metakhronos(60, grades_ps, now=True)
            self.account.updaters['grades'] = grades_ps
            self.account.scheduled['grades'] = ug

            updates.chronomancer.track(us, self.account.name)
            updates.chronomancer.track(ua, self.account.name)
            updates.chronomancer.track(ug, self.account.name)


        schedule = self.account.updaters['schedule'].wait()
        #print(scrape.prettify(schedule))
        schedule = schedule.get(TESTDATE, {})

        # Spawn some class updaters to fill gaps; these won't matter for this page but we should spawn them for when they're needed
        scp = self.account.personal_scraper
        auth = self.account.bb_auth
        for cls in schedule.values():
            if type(cls) is not dict:
                continue
            if cls['real']:
                cid = cls['id']
                if cid not in updates.CLASSES:
                    # Create class updater
                    cps = Poolsafe(
                        updates.dsetter(updates.CLASSES, cid, updates.bb_login_safe(scp.get_class_info, *auth)), cid)
                    cu = updates.chronomancer.monthly(1, cps, now=True)
                    updates.chronomancer.track(cu, cid)
                    updates.CLASS_UPDATERS[cid] = cps
                    updates.CLASS_UPDATERS['_'+str(cid)] = cu

                    # Create class topics updater
                    updates.CLASS_TOPICS[cid] = {}
                    tps = Poolsafe(
                        updates.dsetter(updates.CLASS_TOPICS, cid, updates.bb_login_safe(scp.topics, *auth)), cid
                    )
                    tu = updates.chronomancer.daily(scrape.dt_from_timestr(TESTTIME), tps, now=True)
                    updates.chronomancer.track(tu, cid)
                    updates.TOPICS_UPDATERS[cid] = tps
                    updates.TOPICS_UPDATERS['_'+str(cid)] = tu


        assignments = self.account.updaters['assignments'].wait()
        grades = self.account.updaters['grades'].wait()
        #print(scrape.prettify(assignments))
        #print(scrape.prettify(grades))
        prf = self.account.updaters['profile'].wait()

        periods = []
        spec = ' / '.join(schedule.get('SPECIAL', [])).lower()
        classday = 'Day {}'.format(scrape.get(schedule, 'DAY', 'of No Class')) + (' (Half Day)' if 'dismissal' in spec else '')
        start = None
        end = None
        nextclass = None
        for period, _class in schedule.items():
            if type(_class) is not dict:
                continue

            if _class['real']:
                s = datetime.strptime(_class['start'], '%I:%M %p').time()
                e = datetime.strptime(_class['end'], '%I:%M %p').time()
                n = datetime.strptime('12:30 pm', '%I:%M %p').time()
                if n < s and nextclass is None:
                    start = scrape.striptimezeros(s.strftime('%I:%M'))
                    end = scrape.striptimezeros(e.strftime('%I:%M'))
                    nextclass = period, _class

                periods.append(snippet('classtab', period=period, classname=_class['title']))
            else:
                periods.append(snippet('nullclass', name=period))

        # Generate menu
        menulist = updates.SAGEMENU.get(TESTDATE, ())
        menu = []
        if menulist:
            for item in menulist:
                di = updates.SAGEMENUINFO.get(item, [])
                veg = 'vegitem ' if not any(map(lambda d: d[1] == "Vegetarian", di)) else ''
                menu.append(snippet('menuitem', name=item, veg=veg))

        contains, may_contain, cross = updates.SAGEMENUINFO.get(TESTDATE, ('nothing', 'nothing', ''))

        # Generate announcements
        announcements = [snippet('announcement',
            title=ann.title,
            date=datetime.fromtimestamp(ann.timestamp).strftime('%m/%d/%Y'),
            text='\n'.join(['<p>{}</p>'.format(text) for text in ann.text.split('\n')])
        ) for ann in reversed(info.GENERAL_ANNOUNCEMENTS) if ann.displayed]

        if not announcements:
            announcements = snippet('no-announcement'),

        # Generate assignments
        assignmentlist = []
        for title, assignment in assignments:
            assignmentlist.append(snippet('assignment',
                                          title=title,
                                          due=assignment['due'],
                                          s12='&nbsp;'*12,
                                          assnd=assignment['assigned'],
                                          desc=assignment['desc']))

        # Generate Ma'amad schedule
        maamads = []
        for week in info.MAAMADS:
            if week.is_this_week(TESTDATE):
                for day in week.week:
                    activity, desc = week.get_date(day)
                    dt = datetime.strptime(day, '%m/%d/%Y')
                    maamads.append(snippet('maamad-tab',
                                           title=activity,
                                           desc=desc.replace('\n', '<br>'),
                                           weekday=ISOWEEKDAYNAMES[dt.isoweekday()][:3]+'.',
                                           dayord=ordinal(dt.day)))
                break

        noschool = not periods or 'cancel' in spec or 'close' in spec or 'field day' in spec

        self.response.attach_file('/accounts/landing.html', cache=False,
                                  classday=classday,
                                  next_class_info=snippet('next-class-info-1',
                                                          period=nextclass[0],
                                                          startp=scrape.striptimezeros(nextclass[1]['start']).lower()) if nextclass else 'No school today.' if noschool else 'No more classes today.',
                                  next_class_meta=snippet('next-class-info-2',
                                                           name=nextclass[1]['title'],
                                                           teacher=grades[nextclass[1]['id']]['teacher'],
                                                           email=grades[nextclass[1]['id']]['teacher-email'],
                                                           start=start,
                                                           end=end) if nextclass else snippet('next-class-info-e', msg='Have a lovely day!'),
                                  periods='\n'.join(periods) if periods and not noschool else snippet('no-periods',
                                                                                                      text=(
                                                                                                          'No Classes Today' if not schedule.get('SPECIAL')
                                                                                                              else '<br>'.join(
                                                                                                                  set(schedule['SPECIALFMT'])
                                                                                                              )
                                                                                                          )
                                                                                                      ),
                                  no_school=snippet('red-border') if noschool else '',
                                  announcements='\n'.join(announcements),
                                  allergens=snippet('allergens', contains, may_contain, cross),
                                  prefix=prf['prefix'],
                                  assignments='\n'.join(assignmentlist) if assignmentlist else snippet('no-assignments'),
                                  maamads='\n'.join(maamads) if maamads else snippet('no-maamad'),
                                  menu='\n'.join(menu) if menu else snippet('no-food'))