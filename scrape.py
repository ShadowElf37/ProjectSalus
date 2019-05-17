from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from time import strftime
from bs4 import BeautifulSoup
import platform

class Tab:
    def __init__(self, driver, window):
        self.window: str = window
        self.browser: Browser = driver

    @staticmethod
    def focused(f):
        def dec(self, *args, **kwargs):
            old_tab = self.browser.current_tab()
            if old_tab != self.window: self.focus()
            r = f(self, *args, **kwargs)
            if old_tab != self.window: self.browser.switch_tab_key(old_tab)
            return r
        return dec
    focused = focused.__func__  # Necessary to avoid conflict between decorator and staticmethod

    def focus(self):
        return self.browser.switch_tab_key(self.window)
    def get_tab(self):
        return self.window
    def page_html(self):
        return Browser.soup(self.getElementByTag('html'))
    def is_focused(self):
        return self.browser.current_tab() == self.window

    @focused
    def wait_for(self, ecmethod, timeout=6):
        self.browser.wait_for(ecmethod, timeout)
    @focused
    def wait_for_not(self, ecmethod, timeout=6):
        self.browser.wait_for_not(ecmethod, timeout)

    @focused
    def open(self, url):
        self.browser.open(url)
    get = go = goto = open

    @focused
    def get_title(self):
        return self.browser.get_title()
    @focused
    def await_title_is(self, title, timeout=5):
        return self.browser.await_title_is(title, timeout)
    @focused
    def get_url(self):
        return self.browser.get_url()
    @focused
    def await_url_is(self, url, timeout=5):
        return self.browser.await_url_is(url, timeout)

    @focused
    def run_js(self, js):
        return self.browser.run_js(js)

    @focused
    def getElementById(self, id, timeout=2, multiple=False):
        return self.browser.getElementById(id, timeout, multiple)
    @focused
    def getElementByClass(self, cls, timeout=2, multiple=False):
        return self.browser.getElementById(cls, timeout, multiple)
    @focused
    def getElementByTag(self, tag, timeout=2, multiple=False):
        return self.browser.getElementById(tag, timeout, multiple)
    @focused
    def getElementBySelector(self, css_sel, timeout=2, multiple=False):
        return self.browser.getElementById(css_sel, timeout, multiple)
    @focused
    def findElement(self, by: By, value, timeout=2, multiple=False):
        return self.browser.findElement(by, value, timeout, multiple)

    def close(self):
        self.browser.close_tab_key(self.window)
    def duplicate(self):
        self.browser._new_tab()
        self.browser.get(self.get_url())
    @focused
    def refresh(self):
        return self.browser.refresh()
    @focused
    def back(self):
        return self.browser.back()
    @focused
    def forward(self):
        return self.browser.forward()



class Browser:
    OS = platform.system()
    CTRL = Keys.COMMAND if OS == 'Darwin' else Keys.CONTROL

    def __init__(self):
        self.options = Options()
        self.options.headless = False
        self.driver = webdriver.Firefox(options=self.options)
        self.tab_objects = []

    @staticmethod
    def source(browser_obj) -> str:
        return browser_obj.get_attribute('innerHTML')
    @staticmethod
    def soup(browser_obj) -> BeautifulSoup:
        return BeautifulSoup(Browser.source(browser_obj), 'html.parser')

    def open(self, url) -> Tab:
        self.driver.get(url)
        if len(self.tab_objects) < 1:
            t = Tab(self, self.current_tab())
            self.tab_objects.append(t)
        else:
            t: Tab = self.get_tab_by_key(self.current_tab())
        return t
    get = open

    def wait_for(self, ecmethod, timeout=6):
        return WebDriverWait(self.driver, timeout).until(ecmethod)
    def wait_for_not(self, ecmethod, timeout=6):
        return WebDriverWait(self.driver, timeout).until_not(ecmethod)

    def getElementById(self, id, timeout=2, multiple=False):
        if timeout:
            if multiple:
                return self.wait_for(EC.presence_of_all_elements_located((By.ID, id)), timeout)
            return self.wait_for(EC.presence_of_element_located((By.ID, id)), timeout)
        if multiple:
            self.driver.find_elements_by_id(id)
        return self.driver.find_element_by_id(id)

    def getElementByClass(self, cls, timeout=2, multiple=False):
        if timeout:
            if multiple:
                return self.wait_for(EC.presence_of_all_elements_located((By.CLASS_NAME, cls)), timeout)
            return self.wait_for(EC.presence_of_element_located((By.CLASS_NAME, cls)), timeout)
        if multiple:
            self.driver.find_elements_by_class_name(cls)
        return self.driver.find_element_by_class_name(cls)

    def getElementBySelector(self, css_sel, timeout=2, multiple=False):
        if timeout:
            if multiple:
                return self.wait_for(EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_sel)), timeout)
            return self.wait_for(EC.presence_of_element_located((By.CSS_SELECTOR, css_sel)), timeout)
        if multiple:
            self.driver.find_elements_by_css_selector(css_sel)
        return self.driver.find_element_by_css_selector(css_sel)

    def getElementByTag(self, tag, timeout=2, multiple=False):
        if timeout:
            if multiple:
                return self.wait_for(EC.presence_of_all_elements_located((By.TAG_NAME, tag)), timeout)
            return self.wait_for(EC.presence_of_element_located((By.TAG_NAME, tag)), timeout)
        if multiple:
            self.driver.find_elements_by_tag_name(tag)
        return self.driver.find_elements_by_tag_name(tag)

    def findElement(self, by: By, value, timeout=2, multiple=False):
        if timeout:
            if multiple:
                return self.wait_for(EC.presence_of_all_elements_located((by, value)), timeout)
            return self.wait_for(EC.presence_of_element_located((by, value)), timeout)
        if multiple:
            return self.driver.find_elements(by, value)
        return self.driver.find_element(by, value)

    def await_url_is(self, url, timeout=5):
        return self.wait_for(EC.url_matches(url), timeout)
    def get_url(self):
        return self.driver.current_url

    def await_title_is(self, title, timeout=5):
        return self.wait_for(EC.title_is(title), timeout)
    def get_title(self):
        return self.driver.title

    def get_tab(self, n) -> Tab:
        return self.tab_objects[n]
    def get_tab_by_key(self, key) -> Tab:
        try:
            return next(filter(lambda t: t.window == key, self.tab_objects))
        except StopIteration:
            raise KeyError('Key does not match any tab objects.')
    def _get_tab(self, n) -> str:
        return self.driver.window_handles[n]
    def current_tab(self) -> str:
        return self.driver.current_window_handle
    def await_new_tab(self, timeout=1):
        return self.wait_for(EC.new_window_is_opened(self.driver.window_handles), timeout)
    def _new_tab(self):
        r = self.run_js("window.open('', '_blank')")
        self.switch_last_tab()
        return r
    def new_tab(self, url=None) -> Tab:
        self._new_tab()
        t = Tab(self, self.current_tab())
        self.tab_objects.append(t)
        if url: self.open(url)
        return t
    def switch_tab(self, n):
        try:
            return self.driver.switch_to.window(self._get_tab(n))
        except IndexError:
            return self.switch_last_tab()
    def switch_tab_key(self, tabkey):
        return self.driver.switch_to.window(tabkey)
    def switch_last_tab(self):
        return self.switch_tab(-1)
    def close_tab_key(self, key):
        self.close_tab(self.driver.window_handles.index(key))
        self.tab_objects.remove(self.get_tab_by_key(key))
    def close_tab(self, n=None):
        current = self.current_tab() if n is None else self._get_tab(n)
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

    def is_visible(self, obj):
        return EC.visibility_of(obj)
    def is_invisible(self, obj):
        return EC.invisibility_of_element(obj)

    def run_js(self, js):
        return self.driver.execute_script(js)

    def set_cookies(self, **kwargs):
        self.driver.add_cookie(kwargs)
    def get_cookie(self, k) -> str:
        return self.driver.get_cookie(k)
    def get_cookies(self) -> list:
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


firefox = Browser()
blackbaud = firefox.open('https://emeryweiner.myschoolapp.com/app/student#login')

user = blackbaud.getElementById('Username', 5)
submit = blackbaud.getElementById('nextBtn')
user.send_keys('ykey-cohen')
submit.click()

pwd = blackbaud.getElementById('Password')
pwd.send_keys('Yoproductions3')
submit = blackbaud.getElementById('loginBtn')
submit.click()
blackbaud.await_url_is('https://emeryweiner.myschoolapp.com/app/student#activitystream')

twitter = firefox.new_tab('https://twitter.com')
blackbaud.get('https://emeryweiner.myschoolapp.com/app/student#studentmyday/assignment-center')
twitter.close()

schedule = blackbaud.getElementById('calendar-main-view', 5)
print(firefox.soup(schedule))
firefox.close()
