from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from time import strftime
from bs4 import BeautifulSoup
import platform

class Browser:
    OS = platform.system()
    CTRL = Keys.COMMAND if OS == 'Darwin' else Keys.CONTROL

    def __init__(self):
        self.options = Options()
        self.options.headless = False
        self.driver = webdriver.Firefox(options=self.options)

    @staticmethod
    def source(browser_obj):
        return browser_obj.get_attribute('innerHTML')
    @staticmethod
    def soup(browser_obj):
        return BeautifulSoup(Browser.source(browser_obj), 'html.parser')

    def open(self, url):
        self.driver.get(url)

    def wait_for(self, ecmethod, timeout=6):
        return WebDriverWait(self.driver, timeout).until(ecmethod)
    def wait_for_not(self, ecmethod, timeout=6):
        return WebDriverWait(self.driver, timeout).until_not(ecmethod)

    def getElementById(self, id, timeout=2, multiple=False):
        if timeout:
            if multiple:
                return WebDriverWait(self.driver, timeout).until(EC.presence_of_all_elements_located((By.ID, id)))
            return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((By.ID, id)))
        if multiple:
            self.driver.find_elements_by_id(id)
        return self.driver.find_element_by_id(id)

    def getElementByClass(self, cls, timeout=2, multiple=False):
        if timeout:
            if multiple:
                return WebDriverWait(self.driver, timeout).until(EC.presence_of_all_elements_located((By.CLASS_NAME, cls)))
            return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((By.CLASS_NAME, cls)))
        if multiple:
            self.driver.find_elements_by_class_name(cls)
        return self.driver.find_element_by_class_name(cls)

    def getElementBySelector(self, css_sel, timeout=2, multiple=False):
        if timeout:
            if multiple:
                return WebDriverWait(self.driver, timeout).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_sel)))
            return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_sel)))
        if multiple:
            self.driver.find_elements_by_css_selector(css_sel)
        return self.driver.find_element_by_css_selector(css_sel)

    def getElementByTag(self, tag, timeout=2, multiple=False):
        if timeout:
            if multiple:
                return WebDriverWait(self.driver, timeout).until(EC.presence_of_all_elements_located((By.TAG_NAME, tag)))
            return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, tag)))
        if multiple:
            self.driver.find_elements_by_tag_name(tag)
        return self.driver.find_elements_by_tag_name(tag)

    def await_url_is(self, url, timeout=5):
        return WebDriverWait(self.driver, timeout).until(EC.url_matches(url))
    def get_url(self):
        return self.driver.current_url

    def await_title_is(self, title, timeout=5):
        return WebDriverWait(self.driver, timeout).until(EC.title_is(title))
    def get_title(self):
        return self.driver.title

    def get_tab(self, n):
        return self.driver.window_handles[n]
    def current_tab(self):
        return self.driver.current_window_handle
    def await_new_tab(self, timeout=5):
        return WebDriverWait(self.driver, timeout).until(EC.new_window_is_opened(self.driver.window_handles))
    def new_tab(self):
        r = self.driver.execute_script("window.open('', '_blank')")
        self.switch_last_tab()
        return r
    def switch_tab(self, n):
        try:
            return self.driver.switch_to.window(self.get_tab(n))
        except IndexError:
            return self.switch_last_tab()
    def switch_tab_obj(self, tabobj):
        return self.driver.switch_to.window(tabobj)
    def switch_last_tab(self):
        return self.switch_tab(-1)
    def close_tab(self, n=None):
        current = self.current_tab() if n is None else self.get_tab(n)
        tabs = self.driver.window_handles.copy()
        current_index = tabs.index(current)
        tabs.remove(current)
        for tab in self.driver.window_handles:
            if tab != current:
                self.driver.window_handles.remove(tab)
        self.close()
        for tab in tabs:
            self.driver.window_handles.append(tab)
        self.switch_tab(current_index - 1)

    def get_visible(self, obj):
        return EC.visibility_of(obj)
    def get_invisible(self, obj):
        return EC.invisibility_of_element(obj)

    def do_js(self, js):
        return self.driver.execute_script(js)

    def set_cookies(self, **kwargs):
        self.driver.add_cookie(kwargs)
    def get_cookie(self, k):
        return self.driver.get_cookie(k)
    def get_cookies(self):
        return self.driver.get_cookies()

    def screenshot(self):
        return self.driver.save_screenshot('Selenium Screenshot - {}.png'.format(strftime('%X %D')))

    def refresh(self):
        return self.driver.refresh()
    def back(self):
        return self.driver.back()
    def forward(self):
        return self.driver.forward()

    def close(self):
        return self.driver.close()


test = Browser()
test.open('https://emeryweiner.myschoolapp.com/app/student#login')

user = test.getElementById('Username', 5)
submit = test.getElementById('nextBtn')
user.send_keys('ykey-cohen')
submit.click()

pwd = test.getElementById('Password')
pwd.send_keys('no password for you hehe')
submit = test.getElementById('loginBtn')
submit.click()
test.await_url_is('https://emeryweiner.myschoolapp.com/app/student#activitystream')

test.new_tab()
test.open('https://twitter.com')
test.switch_tab(0)
test.open('https://emeryweiner.myschoolapp.com/app/student#studentmyday/assignment-center')
test.switch_tab(1)
test.open('https://google.com')
test.close_tab()

schedule = test.getElementById('calendar-main-view', 5)
print(test.soup(schedule))
test.close()
