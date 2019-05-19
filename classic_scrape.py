import requests
from bs4 import BeautifulSoup
import json
from html import escape
import datetime

def html(s):
    return BeautifulSoup(s, 'html.parser')


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

    def blackbaud_login(self, user, password, *needed_cookies, **headers):
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

        return directory

    def schedule(self, **headers):
        params = {
            'scheduleDate': '5/17/2019',
            'personaId': 2,
        }
        headers.update(self.default_headers)

        schedule = self.check(requests.get('https://emeryweiner.myschoolapp.com/api/schedule/MyDayCalendarStudentList/',
                                params=params, headers=headers, cookies=self.default_cookies)).json()
        return schedule

    def grades(self, **headers):
        params = {
            'userId': '3510119',
            'schoolYearLabel': '2018 - 2019',
            'memberLevel': 3,
            'persona': 2,
            'durationList': 88330,
            # 'markingPeriodId': 6260,  # optional; I'm suspicious of it so I commented it out
        }
        headers.update(self.default_headers)

        grades = self.check(requests.get('https://emeryweiner.myschoolapp.com/api/datadirect/ParentStudentUserAcademicGroupsGet',
                              params=params, headers=headers, cookies=self.default_cookies))
        return grades.json()

    def assignments(self, **headers):
        # https://emeryweiner.myschoolapp.com/api/DataDirect/AssignmentCenterAssignments/?format=json&filter=1&dateStart=5%2F12%2F2019&dateEnd=5%2F19%2F2019&persona=2&statusList=&sectionList=
        params = {
            'format': 'json',
            'filter': 1,
            'dateStart': '5/12/2019',
            'dateEnd': '5/19/2019',
            'persona': 2,
            'statusList': None,
            'sectionList': None,
        }
        headers.update(self.default_headers)

        assignments = requests.get('https://emeryweiner.myschoolapp.com/api/DataDirect/AssignmentCenterAssignments/',
                                   params=params, headers=headers, cookies=self.default_cookies).json()
        return assignments

    def get_assignment_downloads(self, assignment_id, **headers):
        params = {}
        headers.update(self.default_headers)
        downloads = self.check(requests.get('https://emeryweiner.myschoolapp.com/api/assignment2/read/{}/'.format(assignment_id),
                                 params=params, headers=headers, cookies=self.default_cookies)).json()

        return downloads['DownloadItems']
