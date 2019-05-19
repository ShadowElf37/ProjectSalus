import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import json
from html import escape

def html(s):
    return BeautifulSoup(s, 'html.parser')

target = 2
UA = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36'

bbauth = {
    # Known to be required
    '__RequestVerificationToken_OnSuite': 'KsZTKw2tXnkfa_wBNLHXgBGZidtdqoF818UJWKudpebams4Y9SBRhPfg5_ij-s1QNgcyz5t2UOM07PpN42ua5klWdcye6pgwsZfx0B9zA5E1',
    't': '97ed7a4d-f56b-ba31-0522-60af9d319b6d',

    # Effect unknown, and never required

    #'sd': 'f5a978e7-b644-4d6f-910d-75ffb2dcfc90',
    #'ss': 'a=lPfVrr4ZBywG2nD7es6ywg==',
    #'rxVisitor': '1490698906134PELUKJHSTM43LJJJPTJU2GKAUI00EQIV',
    #'persona': 'student',
    #'bridge': 'action=create&src=webapp&xdb=true',
    #'G_ENABLED_IDPS': 'google'
}

if target == 0:
    params = {
        'userId':'3510119',
        'schoolYearLabel': '2018 - 2019',
        'memberLevel': 3,
        'persona': 2,
        'durationList': 88330,
        #'markingPeriodId': 6260,
    }
    # ? userId = 3510119 & schoolYearLabel = 2018 + -+2019 & memberLevel = 3 & persona = 2 & durationList = 88330 & markingPeriodId = 6260

    headers = {
        'user-agent': UA,
    }

    cookies = {

    }
    cookies.update(bbauth)

    grades = requests.get('https://emeryweiner.myschoolapp.com/api/datadirect/ParentStudentUserAcademicGroupsGet', params=params, headers=headers, cookies=cookies).json()
    print(json.dumps(grades, indent=2))

elif target == 1:
    # https://emeryweiner.myschoolapp.com/api/DataDirect/AssignmentCenterAssignments/?format=json&filter=1&dateStart=5%2F12%2F2019&dateEnd=5%2F19%2F2019&persona=2&statusList=&sectionList=
    params={
        'format': 'json',
        'filter': 1,
        'dateStart': '5/12/2019',
        'dateEnd': '5/19/2019',
        'persona': 2,
        'statusList': None,
        'sectionList': None,
    }

    headers = {
        'user-agent': UA,
    }

    cookies = {

    }
    cookies.update(bbauth)

    assignments = requests.get('https://emeryweiner.myschoolapp.com/api/DataDirect/AssignmentCenterAssignments/', params=params, headers=headers, cookies=cookies).json()
    downloads = requests.get('https://emeryweiner.myschoolapp.com/api/assignment2/read/10928225/', params=params, headers=headers, cookies=cookies).json()

    print(json.dumps(assignments[-4], indent=2))
    print(json.dumps(downloads['DownloadItems'], indent=2))

elif target == 2:
    # http://www.sagedining.com/intranet/apps/mb/pubasynchhandler.php
    params = {
        'unitId': 'S0097',
        'mbMenuCardinality': 9999,
    }

    headers = {
        'user-agent': UA,
    }

    cookies = {

    }

    menu = requests.get('http://www.sagedining.com/intranet/apps/mb/pubasynchhandler.php', params=params, headers=headers, cookies=cookies).json()

    print(json.dumps(menu, indent=2))