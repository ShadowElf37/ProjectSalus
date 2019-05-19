import requests
from bs4 import BeautifulSoup
import json
from html import escape, unescape
import datetime

def html(s):
    return BeautifulSoup(s, 'html.parser')

def todaystr():
    return datetime.datetime.now().strftime('%m/%d/%Y')

def last_sunday(from_date=datetime.datetime.now()):
    return from_date - datetime.timedelta(days=from_date.weekday()+1)

def next_saturday(from_date=datetime.datetime.now()):
    return from_date + datetime.timedelta(days=6-(from_date.weekday()+1))

class Scraper:
    def __init__(self):
        self.useragent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36'
        self.default_headers = {'user-agent': self.useragent}
        self.default_cookies = {}
        self.default_data = {}

    @staticmethod
    def check(resp: requests.Response) -> requests.Response:
        if resp.status_code != 200:
            raise ValueError('Request failed with {}: {}'.format(resp.status_code, resp.text))
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
        cookies = {k:login.cookies[k] for k in needed_cookies}
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

        for grade in range(6, 13, 2):  # Site can only handle 200 results per search, so it must be divided into 3 2-grade searches
            grades = '3261_{}|3261_{}'.format(str(grade), str(grade + 1))
            params.update(facets=grades)
            resp = self.check(requests.get('https://emeryweiner.myschoolapp.com/api/directory/directoryresultsget',
                               params=params, headers=headers, cookies=self.default_cookies))
            directory += resp.json()

        directory = {('{} {}'.format(person['FirstName'], person['LastName'])): {k2: (person[k1].strip() if type(person.get(k1)) is str else person.get(k1)) for k1,k2 in (
            ('UserID', 'id'),
            ('Email', 'email'),
            ('AddressLine1', 'address'),
            ('City', 'city'),
            ('State', 'state'),
            ('Zip', 'zip'),
            ('HomePhone', 'homephone'),
            ('CellPhone', 'cellphone'),
            ('GradYear', 'year'),
            ('GradeDisplay', 'grade'),
            ('PreferredAddressLat', 'addrlatitude'),
            ('PreferredAddressLng', 'addrlongitude')
        )} for person in directory}

        return directory

    def schedule(self, date=datetime.date.today().strftime('%m/%d/%Y'), **headers):
        params = {
            'scheduleDate': date,
            'personaId': 2,
        }
        headers.update(self.default_headers)

        schedule = self.check(requests.get('https://emeryweiner.myschoolapp.com/api/schedule/MyDayCalendarStudentList/',
                                params=params, headers=headers, cookies=self.default_cookies)).json()

        schedule = {period['Block']: {
            'class': period['CourseTitle'],
            'room': period['RoomNumber'],
            'building': period['BuildingName'],
            'start': period['MyDayStartTime'],
            'end': period['MyDayEndTime'],
            'teacher': period['Contact'],
            'teacher-email': period['ContactEmail']
        } for period in schedule}

        return schedule

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
        # more detailed info at https://emeryweiner.myschoolapp.com/api/datadirect/GradeBookPerformanceAssignmentStudentList/?sectionId=89628670&markingPeriodId=6260&studentUserId=3510119

        grades = {_class['sectionidentifier']: {
            'id': _class['sectionid'],
            'teacher': _class['groupownername'],
            'teacher-email': _class['groupowneremail'].lower(),
            'semester': _class['currentterm'],
            'grade': _class['cumgrade'],
        } for _class in grades}

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
            'class-name': ass['groupname'],
            'id': ass['assignment_id'],
            'assigned': ass['date_assigned'],
            'due': ass['date_due'],
            'desc': html(ass['long_description'].replace('<br />', ' \n') if ass.get('long_description') else '').text,
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
    bb = BlackbaudScraper()
    print('LOGGING IN...')
    bb.login('ykey-cohen', 'Yoproductions3', 't')

    print('\nPROFILE')
    print('=' * 20)
    print(json.dumps(bb.directory()['Yovel Key-Cohen'], indent=4))
    print('\nSCHEDULE FOR 5/20/19')
    print('=' * 20)
    print(json.dumps(list(bb.schedule('05/20/2019').keys()), indent=4))
    print('\nMATH GRADE')
    print('=' * 20)
    print(json.dumps(bb.grades('3510119')['Pre-Calculus Honors - C (C)'], indent=4))
    print('\nHEBREW HOMEWORK FROM FRIDAY')
    print('=' * 20)
    print(json.dumps({'MAAMAR- READ BEVAKASHA': bb.assignments()['MAAMAR- READ BEVAKASHA']}, indent=4))
    print('\nHEBREW HOMEWORK ATTACHMENTS')
    print('=' * 20)
    print(json.dumps(bb.get_assignment_downloads(bb.assignments()['MAAMAR- READ BEVAKASHA']['id']), indent=4))