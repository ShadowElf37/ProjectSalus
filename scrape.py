#!/usr/bin/env python3
import requests
import json
import re
import datetime
from time import time, sleep
from bs4 import BeautifulSoup
import calendar
from html import escape, unescape
from server.threadpool import Minisafe

def html(s):
    return BeautifulSoup(s, 'html.parser')
def soup_without(soup: BeautifulSoup, **fields):
    """Fields can be (tag) name=, text=, etc. - whatever's used by BeautifulSoup.find_all()"""
    items = soup.find_all(**fields)
    for elem in items:
        elem.extract()
    return soup

def todaystr():
    return datetime.datetime.now().strftime('%m/%d/%Y')

def now():
    return datetime.datetime.now()

def dt_from_timestr(t):
    return datetime.datetime.strptime(t, '%I:%M %p').time()

def sun_era():
    n = now()
    return 'morning' if n.hour < 12 else 'afternoon' if n.hour < 17 else 'evening'

def last_sunday(from_date=datetime.datetime.now()):
    offset = from_date.isoweekday()
    if from_date.isoweekday() == 7:
        offset = 0
    return from_date - datetime.timedelta(days=offset)

def next_saturday(from_date=datetime.datetime.now()):
    offset = from_date.isoweekday()
    if from_date.isoweekday() == 7:
        offset = 0
    return from_date + datetime.timedelta(days=6-offset)

def week_of(dt: datetime.datetime):
    return [last_sunday(dt) + datetime.timedelta(days=i) for i in range(7)]

def firstlast_of_month(deltaMonth=0):
    n = datetime.datetime.now()
    n = delta_months(n, deltaMonth)
    return n.replace(day=1), n.replace(day=calendar.monthrange(n.year, n.month)[1])
flmsf = lambda i, dm=0: Minisafe(lambda f: f(dm)[i], firstlast_of_month)

def delta_months(dt: datetime.datetime, n=0):
    y, m = divmod(dt.month + n, 12)
    if m == 0: m = 12
    y += dt.year
    d = min(calendar.monthrange(y, m)[1], dt.day)
    return dt.replace(year=y, month=m, day=d)

def split_date_range_into_months(startdt, enddt):
    months = []
    y = m = 0
    i = startdt.month
    while m != enddt.month or y != enddt.year:
        y, m = divmod(i, 12)
        y += startdt.year
        m = 12 if m is 0 else m
        months.append((
            datetime.datetime(month=m, year=y, day=1),
            datetime.datetime(month=m, year=y, day=calendar.monthrange(y, m)[1])
        ))
        i += 1
    return months

def prettify(jsonobj, indent=4):
    return json.dumps(jsonobj, indent=indent)

def bbdt(date_time_string):
    return datetime.datetime.strptime(date_time_string, '%m/%d/%Y %I:%M %p')

def format_phone_num(string: str):
    if not string: return ''
    if string.count('-') < 2:
        string = string.replace('-', '')
        return '-'.join((string[:3], string[3:6], string[6:]))
    return string

def format_class_name(string: str):
    # ([0-9][a-z]* (Sem)*)|   Catches '2nd Sem' etc.
    periodnames = re.findall('( - [A-Z0-9]*( \(.*\))*( \([A-Z]\))*)|( \(.*\))', string)
    for bad in periodnames:
        for bad in bad:
            string = string.replace(bad, '')
    return string

def period_from_name(string: str):
    try:
        return re.findall('((?! \()([^(]+)(?=\)))', string)[-1][0]
    except IndexError:
        return string

def get(dict, k, default=None):
    return dict.get(k, default) if dict.get(k) else default

def striptimezeros(string):
    if string[0] == '0':
        return string[1:]
    return string


class StatusError(BaseException):
    COUNTER = 0
    def __init__(self, *args):
        StatusError.COUNTER += 1
        super().__init__(*args)

class Scraper:
    def __init__(self):
        self.useragent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36'
        self.default_headers = {'user-agent': self.useragent}
        self.cookies = {}
        self.default_data = {}

    @staticmethod
    def check(resp: requests.Response) -> requests.Response:
        if resp.status_code != 200:
            raise StatusError('Request failed with {}: {}'.format(resp.status_code, resp.text))
        return resp

class SageScraper(Scraper):
    AVOID = {
        # Contains allergen:
        "1": (0, "Wheat"),
        "11": (0, "Gluten"),
        "21": (0, "Egg"),
        "31": (0, "Fish"),
        "41": (0, "Milk"),
        "51": (0, "Soy"),
        "61": (0, "Sesame"),
        "71": (0, "Shellfish"),
        "81": (0, "Shellfish"),
        "91": (0, "Mustard"),
        "101": (0, "Peanut"),
        "111": (0, "Tree Nut"),
        "121": (0, "Tree Nut"),
        "131": (0, "Sulfites"),
        # May contain allergen:
        "201": (1, "Wheat"),
        "211": (1, "Gluten"),
        "221": (1, "Egg"),
        "231": (1, "Fish"),
        "241": (1, "Milk"),
        "251": (1, "Soy"),
        "261": (1, "Sesame"),
        "271": (1, "Shellfish"),
        "281": (1, "Shellfish"),
        "291": (1, "Mustard"),
        # Subject to cross-contamination:
        "481": (2, "Fryer"),
        # Violates lifestyle:
        "601": (3, "Vegetarian"),
        "611": (3, "Vegan"),
    }

    def inst_menu(self, **headers):
        # http://www.sagedining.com/intranet/apps/mb/pubasynchhandler.php
        params = {
            'unitId': 'S0097',
            'mbMenuCardinality': 9999,
        }
        headers.update(self.default_headers)

        # TESTING PURPOSES - Sage menu isn't available during summer
        sleep(2)
        menu = json.loads(escape(open('samplemenu.json', 'r').read(), quote=False))
        #menu = self.check(requests.get('http://www.sagedining.com/intranet/apps/mb/pubasynchhandler.php', params=params, headers=headers, cookies=self.cookies)).json()

        if 'menu' not in menu:
            return {}, {}
        # The start date written in the file is a lie; it will start on Sunday of the week of the start date
        start_date = last_sunday(datetime.datetime.strptime(menu['menu']['config']['meta']['menuFirstDate'], '%m/%d/%Y'))
        menu_dict = {}
        daycount = 0



        menu_info_dict = {}
        for week in menu['menu']['menu']['items']:
            for day in week:
                if type(day) is list:  # "Daily Offerings" is stored at the very end in a dict - we don't care about that
                    soups, salads, sandwiches, entrees, *_ = day[1]
                    newdate = (start_date + datetime.timedelta(days=daycount)).strftime('%m/%d/%Y')

                    # Get food items
                    menu_dict[newdate] = [dish['a'] for dish in entrees]

                    # Get allergen info
                    for dish in entrees:
                        if dish['a'] not in menu_info_dict:
                            menu_info_dict[dish['a']] = tuple({self.AVOID.get(al) for al in dish['al'] if self.AVOID.get(al)})

                    # Render ready-made general allergen strings for the client to enjoy
                    allergen_0 = sorted(
                        {al[1] for item in menu_dict[newdate] for al in menu_info_dict.get(item, []) if
                         al[0] == 0})  # Contains
                    allergen_1 = sorted(
                        {al[1] for item in menu_dict[newdate] for al in menu_info_dict.get(item, []) if
                         al[0] == 1})  # May contain
                    allergen_2 = sorted(
                        {al[1] for item in menu_dict[newdate] for al in menu_info_dict.get(item, []) if
                         al[0] == 2})  # Cross contamination warning

                    contains = (', '.join(allergen_0[:-1]) + ', and ' + allergen_0[-1]) if len(allergen_0) > 2 \
                        else ' and '.join(allergen_0) if len(allergen_0) == 2 \
                        else allergen_0[0] if len(allergen_0) == 1 \
                        else 'nothing'
                    may_contain = (', '.join(allergen_1[:-1]) + ', and ' + allergen_1[-1]) if len(allergen_1) > 2 \
                        else ' and '.join(allergen_1) if len(allergen_1) == 2 \
                        else allergen_1[0] if len(allergen_1) == 1 \
                        else 'nothing'
                    cross = 'Some food is subject to cross-contamination in oil.' if allergen_2 else ''

                    menu_info_dict[newdate] = [contains, may_contain, cross]

                    daycount += 1

        self.menu = menu_dict
        self.menu_info = menu_info_dict
        return menu_dict, menu_info_dict

    def get_menu(self):
        if not getattr(self, 'menu', None):
            return None
        return self.menu
    def get_menu_info(self):
        if not getattr(self, 'menu_info', None):
            return None
        return self.menu_info


class BlackbaudScraper(Scraper):
    VALIDATOR = {
        # Very much required
        't': '4f2f3fec-4cf6-e98e-eea2-59b378226873',
        # Never required, and appear to be rather static; sd and ss are returned by login cookie
        '__RequestVerificationToken_OnSuite': 'KsZTKw2tXnkfa_wBNLHXgBGZidtdqoF818UJWKudpebams4Y9SBRhPfg5_ij-s1QNgcyz5t2UOM07PpN42ua5klWdcye6pgwsZfx0B9zA5E1',
        'sd': 'f5a978e7-b644-4d6f-910d-75ffb2dcfc90',
        'ss': 'a=lPfVrr4ZBywG2nD7es6ywg==',
        'rxVisitor': '1490698906134PELUKJHSTM43LJJJPTJU2GKAUI00EQIV',
        'persona': 'student',
        'bridge': 'action=create&src=webapp&xdb=true',
        'G_ENABLED_IDPS': 'google'
    }

    def login(self, user, password, *extra_needed_cookies, **headers):
        # Provide 't' in needed_cookies
        data = {
            'From': None,
            'InterfaceSource': 'WebApp',
            'Password': password,
            'Username': user
        }
        headers.update(self.default_headers)

        needed_cookies = ('t',) + extra_needed_cookies

        login = self.check(requests.post('https://emeryweiner.myschoolapp.com/api/SignIn',
                              headers=headers, data=data))
        cookies = {k:login.cookies.get(k) for k in needed_cookies}
        self.cookies.update(cookies)
        return cookies

    def calendar_filters(self, start_date=flmsf(0), end_date=flmsf(1), **headers):
        #https://emeryweiner.myschoolapp.com/api/mycalendar/list/?startDate=03%2F30%2F2019&endDate=05%2F04%2F2019&settingsTypeId=1&calendarSetId=1
        params = {
            'startDate': Minisafe.test(start_date).strftime('%m/%d/%Y'),
            'endDate': Minisafe.test(end_date).strftime('%m/%d/%Y'),
            'settingsTypeId': 1,
            'calendarSetId': 1
        }
        headers.update(self.default_headers)

        filters = self.check(requests.get('https://emeryweiner.myschoolapp.com/api/mycalendar/list/',
                                                 params=params, headers=headers, cookies=self.cookies)).json()

        filters = {group['Calendar']:{
            f['FilterName']:f['CalendarId'] for f in group['Filters']
        } for group in filters}

        return filters

    def sports_calendar(self, start_date=flmsf(0), end_date=flmsf(1), **headers):
        params = {
            'startDate': Minisafe.test(start_date).strftime('%m/%d/%Y'),
            'endDate': Minisafe.test(start_date).strftime('%m/%d/%Y'),
            'filterString': ','.join(self.calendar_filters(start_date, end_date)['School Athletics'].values()),
            'showPractice': False
        }
        headers.update(self.default_headers)

        calendar_items = self.check(requests.get('https://emeryweiner.myschoolapp.com/api/mycalendar/events',
                                                 params=params, headers=headers, cookies=self.cookies)).json()

        calendar_items = [{
            'type': item.get('EventType'),
            'sport': item['GroupName'],
            'vs': item['Opponent'],
            'homeaway': get(item, 'HomeAway', 'Unknown'),
            'location': get(item, 'Location', 'EWS'),
            'date': bbdt(item['StartDate']).strftime('%m/%d/%Y'),
            'time': bbdt(item['StartDate']).strftime('%I:%M %p'),
            'cancelled': item['Cancelled'],
            'id': item['EventId'],
            'results': ({
                'home':int(item['Results'][0]['Score']) if item['Results'][0]['Score'] else None,
                'away':int(item['Results'][0]['ScoreVs']) if item['Results'][0]['ScoreVs'] else None
            } if item.get('Results') else {'home': None, 'away': None})
        } for item in calendar_items]

        return calendar_items

    def directory(self, **headers):
        params = {
            'directoryId': 1282,
            'searchVal': None,
            'facets': None,
            'searchAll': False,
        }
        headers.update(self.default_headers)
        directory = []

        for grade in range(6, 13, 2):  # Site can only handle 200 results per search, so it must be divided into 4 2-grade searches
            grades = '3261_{}|3261_{}'.format(str(grade), str(grade + 1))
            params.update(facets=grades)
            resp = self.check(requests.get('https://emeryweiner.myschoolapp.com/api/directory/directoryresultsget',
                                           params=params, headers=headers, cookies=self.cookies))
            directory += resp.json()

        directory = {('{} {}'.format(person['FirstName'], person['LastName'])): {
            'id': person.get('UserID'),
            'email' : person.get('Email', '').lower(),
            'address': person.get('AddressLine1'),
            'city': person.get('City'),
            'state': person.get('State'),
            'zip': person.get('Zip'),
            'home': format_phone_num(person.get('HomePhone', '').strip()),
            'cell': format_phone_num(person.get('CellPhone', '').strip()),
            'year': person.get('GradYear'),
            'grade': person.get('GradeDisplay'),
            'addrlatitude': person.get('PreferredAddressLat', 0.0),
            'addrlongitude': person.get('PreferredAddressLng', 0.0),
        } for person in directory}

        return directory

    def teacher_directory(self, **headers):
        #https://emeryweiner.myschoolapp.com/api/directory/directoryresultsget?directoryId=1285&searchVal=&facets=&searchAll=false
        params = {
            'directoryId': 1285,
            'searchVal': None,
            'facets': None,
            'searchAll': False,
        }
        headers.update(self.default_headers)

        resp = self.check(requests.get('https://emeryweiner.myschoolapp.com/api/directory/directoryresultsget',
                                       params=params, headers=headers, cookies=self.cookies)).json()

        directory = {('{} {}'.format(person['FirstName'], person['LastName'])): {
            'id': person['UserID'],
            'prefix': person.get('Prefix', ''),
            'email': person.get('Email', '').lower().replace('mailto:', ''),
            'phone': person.get('OfficePhone', '').strip(),
            'dept': person.get('DepartmentDisplay', '').split(', ')
        } for person in resp}

        return directory

    def dir_details(self, userid, *extra_data_fields, **headers):
        #https://emeryweiner.myschoolapp.com/api/user/4201127/?propertylist=FieldsToNull%2CLastName%2CFirstName%2CMiddleName%2COtherLastName%2CPrefix%2CSuffix%2CMaidenName%2CNickName%2CDisplayName%2CGender%2CBirthDate%2CEmail%2CBirthPlace%2CStudentId%2CLockerNbr%2CLockerCombo%2CMailboxNbr
        params = {
            'propertyList': ','.join(('LastName', 'FirstName', 'MiddleName', 'Prefix', 'Gender', 'BirthDate', 'Email') + extra_data_fields)
        }
        headers.update(self.default_headers)

        resp = self.check(requests.get('https://emeryweiner.myschoolapp.com/api/user/{}/'.format(userid),
                                       params=params, headers=headers, cookies=self.cookies)).json()

        g = resp.get('Gender', '').lower()
        entry = {
            'name': resp['FirstName'] + ' ' + resp['LastName'],
            'first': resp['FirstName'],
            'last': resp['LastName'],
            'middle': resp.get('MiddleName', ''),
            'prefix': get(resp, 'Prefix', {'m':'Mr.','f':'Ms.'}.get(g, 'Undefined')),
            'gender': g,
            'birthdate': bbdt(resp['BirthDate']).strftime('%m/%d/%Y'),
            'email': resp.get('Email', '').lower(),
        }
        entry.update({k:resp.get(k) for k in extra_data_fields})

        return entry

    def topics(self, sectionid, **headers):
        #https://emeryweiner.myschoolapp.com/api/datadirect/sectiontopicsget/89628484/?format=json&active=true&future=false&expired=false&sharedTopics=false
        params = {
            'format': 'json',
            'active': True,
            'future': False,
            'expired': False,
            'sharedTopics': False
        }
        headers.update(self.default_headers)

        resp = self.check(requests.get('https://emeryweiner.myschoolapp.com/api/datadirect/sectiontopicsget/{}/'.format(sectionid),
                                       params=params, headers=headers, cookies=self.cookies)).json()

        topics = {topic['Name']:{
            'id': topic['TopicID'],
            'index': topic['TopicIndexID'],
            'desc': html(get(topic, 'Description', '').replace('<br />', '\n')).text,
            'teacher': topic['TopicAuthorShare'],
            'published': bbdt(topic['PublishDate']).strftime('%m/%d/%Y'),
            'details': {}
        } for topic in resp}

        return topics

    def topic_details(self, topicid, topicidx, **headers):
        # https://emeryweiner.myschoolapp.com/api/datadirect/topiccontentget/482767/?format=json&index_id=987530&id=987530
        params = {
            'format': 'json',
            'index_id': topicidx
        }
        headers.update(self.default_headers)

        resp = self.check(requests.get('https://emeryweiner.myschoolapp.com/api/datadirect/topiccontentget/{}/'.format(topicid),
                                       params=params, headers=headers, cookies=self.cookies)).json()

        details = {dl['ShortDescription']:{
            'desc': dl.get('LongDescription'),
            'uri': dl.get('FilePath', '')+dl.get('FileName', ''),
            'name': dl.get('FriendlyFileName')
        } for dl in resp}

        return details

    def schedule(self, datestr=Minisafe(todaystr), **headers):
        params = {
            'scheduleDate': Minisafe.test(datestr),
            'personaId': 2,
        }
        headers.update(self.default_headers)

        schedule = self.check(requests.get('https://emeryweiner.myschoolapp.com/api/schedule/MyDayCalendarStudentList/',
                                           params=params, headers=headers, cookies=self.cookies)).json()

        schedule = {period['Block']: {
            'class': format_class_name(period['CourseTitle']),
            'room': period['RoomNumber'],
            'building': period['BuildingName'],
            'start': period['MyDayStartTime'],
            'end': period['MyDayEndTime'],
            'teacher': period['Contact'],
            'teacher-email': period.get('ContactEmail', '').lower(),
            'section': period['SectionId'],
        } for period in schedule}

        return schedule

    def schedule_span(self, uid, start_date=flmsf(0), end_date=flmsf(1), **headers):
        #https://emeryweiner.myschoolapp.com/api/DataDirect/ScheduleList/?format=json&viewerId=3510119&personaId=2&viewerPersonaId=2&start=1558846800&end=1562475600&_=1559936166683
        start_date = Minisafe.test(start_date)
        end_date = Minisafe.test(end_date)
        params = {
            'format': 'json',
            'viewerId': uid,
            'personaId': 2,
            'viewerPersonaId': 2,
            'start': int(start_date.timestamp()),
            'end': int(end_date.timestamp())
        }
        headers.update(self.default_headers)
        """
        schedule = []
        for start,end in split_date_range_into_months(start_date, end_date):
            params['start'] = int(start.timestamp())
            params['end'] = int(end.timestamp())
            print(start, end)
            new = self.check(requests.get('https://emeryweiner.myschoolapp.com/api/DataDirect/ScheduleList/',
                                               params=params, headers=headers, cookies=self.cookies)).json()
            print(new)
            schedule += new"""
        schedule = self.check(requests.get('https://emeryweiner.myschoolapp.com/api/DataDirect/ScheduleList/',
                                          params=params, headers=headers, cookies=self.cookies)).json()

        real = {}
        minday = datetime.datetime.max
        for i, period in enumerate(schedule):
            t = period['title']
            dt = bbdt(period['start'])
            if dt < minday: minday = dt
            date = dt.strftime('%m/%d/%Y')
            data = {
                'start': dt.strftime('%I:%M %p'),
                'end': bbdt(period['end']).strftime('%I:%M %p'),
                'id': period['SectionId'],
                'title': format_class_name(t),
                'real': period_from_name(t) in tuple('ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
                'ORD': i,
            }

            if date not in real:
                real[date] = {'SPECIAL': [], 'SPECIALFMT':[], 'DAY': None}
            if 'Day ' == t[:4] and t[4].isnumeric() and data['id'] is None:
                real[date]['DAY'] = int(re.findall('[0-9]', t)[-1][0])
                continue
            elif period_from_name(t) == 'US':
                real[date]['SPECIAL'].append(t)
                real[date]['SPECIALFMT'].append(format_class_name(t))
                continue

            real[date]['ORD'] = (dt - minday).days
            real[date][period_from_name(t)] = data

        return real

    def get_class_info(self, classid, **headers):
        #https://emeryweiner.myschoolapp.com/api/datadirect/SectionInfoView/?format=json&sectionId=89628671&associationId=1
        params = {
            'format': 'json',
            'sectionId': classid,
            'associationId': 1,
        }
        headers.update(self.default_headers)

        info = self.check(requests.get('https://emeryweiner.myschoolapp.com/api/DataDirect/SectionInfoView/',
                                       params=params, headers=headers, cookies=self.cookies)).json()
        if type(info) is list:
            info = info[0]

        info = {
            'id': classid,
            'name': info['GroupName'],
            'period': info['Block'],
            'desc': info['Description'],
            'teacher': info['Teacher'],
            'teacher-id': info['TeacherId'],
            'room': info['Room']
        }

        return info


    def grades(self, userid, **headers):
        params = {
            'userId': userid,
            'schoolYearLabel': '2018 - 2019',
            'memberLevel': 3,
            'persona': 2,
            'durationList': 88330,
            # 'markingPeriodId': 6260,  # optional; I'm suspicious of it so I commented it out
        }
        headers.update(self.default_headers)

        grades = self.check(requests.get('https://emeryweiner.myschoolapp.com/api/datadirect/ParentStudentUserAcademicGroupsGet',
                                         params=params, headers=headers, cookies=self.cookies)).json()
        grades = {_class['sectionid']: {
            'title': format_class_name(_class['sectionidentifier']),
            'teacher': _class['groupownername'],
            'teacher-email': get(_class, 'groupowneremail', '').lower(),
            'semester': int(re.match('[0-9]', _class['currentterm']).group()),
            'average': _class['cumgrade'],
        } for _class in grades}

        return grades

    def get_graded_assignments(self, classid, userid, **headers):
        # more detailed info at https://emeryweiner.myschoolapp.com/api/datadirect/GradeBookPerformanceAssignmentStudentList/?sectionId=89628670&markingPeriodId=6260&studentUserId=3510119
        params = {
            'sectionId': classid,
            'markingPeriodId': 6260,
            'studentUserId': userid,
        }
        headers.update(self.default_headers)

        grades = self.check(requests.get('https://emeryweiner.myschoolapp.com/api/datadirect/GradeBookPerformanceAssignmentStudentList/',
                              params=params, headers=headers, cookies=self.cookies)).json()

        print(grades)
        grades = {ass['AssignmentShortDescription']:{
            'id': ass['AssignmentId'],
            'type': ass['AssignmentType'],
            'points': ass['Points'],
            'max': ass['MaxPoints']
        } for ass in grades}

        return grades

    def assignments(self, start_date=Minisafe(last_sunday), end_date=Minisafe(next_saturday), **headers):
        # https://emeryweiner.myschoolapp.com/api/DataDirect/AssignmentCenterAssignments/?format=json&filter=1&dateStart=5%2F12%2F2019&dateEnd=5%2F19%2F2019&persona=2&statusList=&sectionList=
        params = {
            'format': 'json',
            'filter': 1,
            'dateStart': Minisafe.test(start_date).strftime('%m/%d/%Y'),
            'dateEnd': Minisafe.test(end_date).strftime('%m/%d/%Y'),
            'persona': 2,
            'statusList': None,
            'sectionList': None,
        }
        headers.update(self.default_headers)

        assignments = self.check(requests.get('https://emeryweiner.myschoolapp.com/api/DataDirect/AssignmentCenterAssignments/',
                                   params=params, headers=headers, cookies=self.cookies)).json()

        assignments = {ass['short_description']:{
            'class-id': ass['section_id'],
            'class': format_class_name(ass['groupname']),
            'id': ass['assignment_id'],
            'assigned': bbdt(ass['date_assigned']).strftime('%m/%d/%Y'),
            'due': bbdt(ass['date_due']).strftime('%m/%d/%Y'),
            'desc': html(get(ass, 'long_description', '').replace('<br />', ' \n')).text,
            'links': ass['has_link'],
            'downloads': ass['has_download'],
            'status': 0
        } for ass in assignments}

        return assignments

    def get_assignment_downloads(self, assignment_id, **headers):
        params = {}
        headers.update(self.default_headers)
        downloads = self.check(requests.get('https://emeryweiner.myschoolapp.com/api/assignment2/read/{}/'.format(assignment_id),
                                            params=params, headers=headers, cookies=self.cookies)).json()

        return {d['FriendlyFileName']: d['DownloadUrl'] for d in downloads['DownloadItems']}


if __name__ == '__main__':
    from server.threadpool import Pool, Promise

    bb = BlackbaudScraper()
    print('LOGGING IN...')
    bb.login('ykey-cohen@emeryweiner.org', 'Yoproductions3', 't')

    # directory = Poolsafe(bb.teacher_directory)
    # details = Poolsafe(bb.dir_details, '3509975')
    # schedule = Poolsafe(bb.schedule, '05/29/2019')
    # grades = Poolsafe(bb.grades, '3510119')
    # grades = Poolsafe(bb.get_graded_assignments, 89628484, 3510119)
    schedule = Promise(bb.schedule_span, '3510119', start_date=firstlast_of_month(-2)[0], end_date=firstlast_of_month(0)[1])
    # assignments = Poolsafe(bb.assignments)
    # topics = Poolsafe(bb.topics, '89628484')
    # calendar = Poolsafe(bb.sports_calendar)
    # cinfo = Poolsafe(bb.get_class_info, 89628484)
    tp = Pool(8)
    tp.launch()
    tp.pushps(schedule)

    r = schedule.wait()
    # print(prettify(r))
