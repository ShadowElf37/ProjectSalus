import requests
import json
import re
import datetime
from time import time
from bs4 import BeautifulSoup

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

def last_sunday(from_date=datetime.datetime.now()):
    return from_date - datetime.timedelta(days=from_date.weekday()+1)

def next_saturday(from_date=datetime.datetime.now()):
    return from_date + datetime.timedelta(days=6-(from_date.weekday()+1))

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


class StatusError(BaseException):...

class Scraper:
    def __init__(self):
        self.useragent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36'
        self.default_headers = {'user-agent': self.useragent}
        self.default_cookies = {}
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

        menu = self.check(requests.get('http://www.sagedining.com/intranet/apps/mb/pubasynchhandler.php',
                            params=params, headers=headers, cookies=self.default_cookies)).json()

        if 'menu' not in menu:
            return {}, {}
        start_date = datetime.datetime.strptime(menu['menu']['config']['meta']['menuFirstDate'], '%m/%d/%Y')
        # The start date is a lie; it will start on Sunday of the week of the start date
        start_date -= datetime.timedelta(days=start_date.weekday() + 1)  # Python's datetime uses Monday as first day of week for some reason
        menu_dict = {}
        daycount = 0

        menu_info_dict = {}
        for week in menu['menu']['menu']['items']:
            for day in week:
                if type(day) is list:  # "Daily Offerings" is stored at the very end in a dict - we don't care about that
                    soups, salads, sandwiches, entrees, *_ = day[1]
                    menu_dict[(start_date + datetime.timedelta(days=daycount)).strftime('%m/%d/%Y')] = [(dish['a']) for dish
                                                                                                        in entrees]
                    for dish in entrees:
                        if dish['a'] not in menu_info_dict:
                            menu_info_dict[dish['a']] = tuple({self.AVOID.get(al) for al in dish['al'] if self.AVOID.get(al)})

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
        # Might be sometimes required? I can't remember and my requests work
        '__RequestVerificationToken_OnSuite': 'KsZTKw2tXnkfa_wBNLHXgBGZidtdqoF818UJWKudpebams4Y9SBRhPfg5_ij-s1QNgcyz5t2UOM07PpN42ua5klWdcye6pgwsZfx0B9zA5E1',
        # Never required, and appear to be rather static; sd and ss are returned by login cookie
        'sd': 'f5a978e7-b644-4d6f-910d-75ffb2dcfc90',
        'ss': 'a=lPfVrr4ZBywG2nD7es6ywg==',
        'rxVisitor': '1490698906134PELUKJHSTM43LJJJPTJU2GKAUI00EQIV',
        'persona': 'student',
        'bridge': 'action=create&src=webapp&xdb=true',
        'G_ENABLED_IDPS': 'google'
    }

    def login(self, user, password, *needed_cookies, **headers):
        # Provide 't' in needed_cookies
        data = {
            'From': None,
            'InterfaceSource': 'WebApp',
            'Password': password,
            'Username': user
        }
        headers.update(self.default_headers)

        login = self.check(requests.post('https://emeryweiner.myschoolapp.com/api/SignIn',
                              headers=headers, data=data))
        cookies = {k:login.cookies.get(k) for k in needed_cookies}
        self.default_cookies.update(cookies)
        return cookies

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
                               params=params, headers=headers, cookies=self.default_cookies))
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
                                       params=params, headers=headers, cookies=self.default_cookies)).json()

        directory = {('{} {}'.format(person['FirstName'], person['LastName'])): {
            'id': person['UserID'],
            'title': person.get('Prefix', ''),
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
                                       params=params, headers=headers, cookies=self.default_cookies)).json()

        g = resp.get('Gender', 'o').lower()
        entry = {
            'name': resp['FirstName'] + ' ' + resp['LastName'],
            'first': resp['FirstName'],
            'last': resp['LastName'],
            'middle': resp.get('MiddleName', ''),
            'prefix': get(resp, 'Prefix', ('Mr.' if g == 'm' else 'Ms.' if g == 'f' else '')),
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
                                       params=params, headers=headers, cookies=self.default_cookies)).json()

        topics = {topic['Name']:{
            'id': topic['TopicID'],
            'index-id': topic['TopicIndexID'],
            'desc': html(get(topic, 'Description', '').replace('<br />', '\n')).text,
            'teacher': topic['TopicAuthorShare'],
            'published': bbdt(topic['PublishDate']).strftime('%m/%d/%Y')
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
                                       params=params, headers=headers, cookies=self.default_cookies)).json()

        details = {dl['ShortDescription']:{
            'desc': dl.get('LongDescription'),
            'uri': dl.get('FilePath', '')+dl.get('FileName', ''),
            'name': dl.get('FriendlyFileName')
        } for dl in resp}

        return details

    def schedule(self, date=todaystr(), **headers):
        params = {
            'scheduleDate': date,
            'personaId': 2,
        }
        headers.update(self.default_headers)

        schedule = self.check(requests.get('https://emeryweiner.myschoolapp.com/api/schedule/MyDayCalendarStudentList/',
                                params=params, headers=headers, cookies=self.default_cookies)).json()

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

    def schedule_span(self, uid, start_date=datetime.datetime.now() - datetime.timedelta(days=10), end_date=datetime.datetime.now() + datetime.timedelta(days=10), **headers):
        #https://emeryweiner.myschoolapp.com/api/DataDirect/ScheduleList/?format=json&viewerId=3510119&personaId=2&viewerPersonaId=2&start=1558846800&end=1562475600&_=1559936166683
        params = {
            'format': 'json',
            'viewerId': uid,
            'personaId': 2,
            'viewerPersonaId': 2,
            'start': start_date.timestamp(),
            'end': end_date.timestamp(),
        }
        headers.update(self.default_headers)

        schedule = self.check(requests.get('https://emeryweiner.myschoolapp.com/api/DataDirect/ScheduleList/',
                                           params=params, headers=headers, cookies=self.default_cookies)).json()

        real = {}
        for period in schedule:
            t = period['title']
            dt = bbdt(period['start'])
            date = dt.strftime('%m/%d/%Y')
            data = {
                'start': dt.strftime('%I:%M %p'),
                'end': bbdt(period['end']).strftime('%I:%M %p'),
                'id': period['SectionId'],
                'title': format_class_name(t)
            }
            if date not in real:
                real[date] = {}
            if period_from_name(t) == 'US' and data['id'] is None:
                real[date]['DAY'] = int(re.findall('[0-9]', t)[-1][0])
                continue
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

        info = self.check(requests.get('https://emeryweiner.myschoolapp.com/api/DataDirect/ScheduleList/',
                                           params=params, headers=headers, cookies=self.default_cookies)).json()

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
                              params=params, headers=headers, cookies=self.default_cookies)).json()
        grades = {format_class_name(_class['sectionidentifier']): {
            'id': _class['sectionid'],
            'teacher': _class['groupownername'],
            'teacher-email': _class['groupowneremail'],
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

        grades = requests.get('https://emeryweiner.myschoolapp.com/api/datadirect/GradeBookPerformanceAssignmentStudentList/',
                              params=params, headers=headers, cookies=self.default_cookies).json()

        grades = {ass['AssignmentShortDescription']:{
            'id': ass['AssignmentId'],
            'type': ass['AssignmentType'],
            'points': ass['Points'],
            'max': ass['MaxPoints']
        } for ass in grades}

        return grades

    def assignments(self, start_date=last_sunday().strftime('%m/%d/%Y'), end_date=next_saturday().strftime('%m/%d/%Y'), **headers):
        # https://emeryweiner.myschoolapp.com/api/DataDirect/AssignmentCenterAssignments/?format=json&filter=1&dateStart=5%2F12%2F2019&dateEnd=5%2F19%2F2019&persona=2&statusList=&sectionList=
        params = {
            'format': 'json',
            'filter': 1,
            'dateStart': start_date,
            'dateEnd': end_date,
            'persona': 2,
            'statusList': None,
            'sectionList': None,
        }
        headers.update(self.default_headers)

        assignments = requests.get('https://emeryweiner.myschoolapp.com/api/DataDirect/AssignmentCenterAssignments/',
                                   params=params, headers=headers, cookies=self.default_cookies).json()

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
                                 params=params, headers=headers, cookies=self.default_cookies)).json()

        return {d['FriendlyFileName']: d['DownloadUrl'] for d in downloads['DownloadItems']}


if __name__ == '__main__':
    from server.threadpool import Pool, Poolsafe

    t = time()
    bb = BlackbaudScraper()
    print('LOGGING IN...')
    bb.login('ykey-cohen@emeryweiner.org', 'Yoproductions3', 't')

    # directory = Poolsafe(bb.teacher_directory)
    # details = Poolsafe(bb.dir_details, '3509975')
    schedule = Poolsafe(bb.schedule, '05/29/2019')
    # grades = Poolsafe(bb.grades, '3510119')
    # schedule = Poolsafe(bb.schedule_span, '3510119')
    # assignments = Poolsafe(bb.assignments)
    # topics = Poolsafe(bb.topics, '89628484')
    tp = Pool(8)
    tp.launch()
    tp.pushps(schedule)

    mydir = schedule.wait()
    print(prettify(mydir))
