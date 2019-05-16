from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup

def simple_get(url):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None.
    """
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None

    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None


def is_good_response(resp, type='html'):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers.get('Content-Type', '').lower()
    return (resp.status_code == 200
            and content_type is not ''
            and content_type.find(type) > -1)


def log_error(e):
    """
    It is always a good idea to log errors.
    This function just prints them, but you can
    make it do anything.
    """
    print(e)


def htmlobj(url):
    return BeautifulSoup(simple_get(url), 'html.parser')
def html_fromtext(text):
    return BeautifulSoup(text, 'html.parser')


# print(htmlobj('http://www.sagedining.com/menus/emeryweiner').find("div", {"id": "sageMbDailyViewFrame"}))

import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
print('Starting.')
driver = webdriver.Firefox()
print('Fetching.')
#driver.get("http://www.sagedining.com/menus/emeryweiner")
#assert "SAGE" in driver.title
#print('Waiting for element.')
#elem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "sageMbDailyViewFrame")))

driver.get('https://emeryweiner.myschoolapp.com/app/student#login')
user = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "Username")))
user.send_keys('ykey-cohen')
submit = driver.find_element_by_id('nextBtn')
submit.click()
pwd = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "Password")))
pwd.send_keys('Yoproductions3')
submit = driver.find_element_by_id('loginBtn')
submit.click()
WebDriverWait(driver, 5).until(EC.url_matches('https://emeryweiner.myschoolapp.com/app/student#activitystream'))
driver.get('https://emeryweiner.myschoolapp.com/app/student#studentmyday/assignment-center')
schedule = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "calendar-main-view")))
print(html_fromtext(schedule.get_attribute('innerHTML')))
# elem = driver.find_element_by_id("email")
# elem = driver.find_element_by_id("pass")
# elem.send_keys(Keys.RETURN)
driver.close()
