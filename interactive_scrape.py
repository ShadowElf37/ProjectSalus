from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from time import strftime, time, sleep
from server.threadpool import Pool
from bs4 import BeautifulSoup
import platform

def wait(conditionf):
    while not conditionf():
        sleep(0.0001)

class Element:
    def __init__(self, elem, tab):
        self.browser = tab.browser
        self.tab = tab
        self.elem = elem
        self.inner = self.check_inner()
        self.outer = self.check_outer()

    @staticmethod
    def focused(f):
        def dec(self, *args, **kwargs):
            old_tab = self.browser.current_tab()
            if old_tab != self.tab.window: self.tab.focus()
            # self.browser.scroll_to(self.elem)
            r = f(self, *args, **kwargs)
            if old_tab != self.tab.window: self.browser.switch_tab_key(old_tab)
            return r
        return dec
    focused = focused.__func__

    @focused
    def scroll_to(self):
        self.browser.scroll_to(self.elem)

    def ec_is_visible(self):
        return EC.visibility_of(self.elem)
    def ec_is_invisible(self):
        return EC.invisibility_of_element(self.elem)
    @focused
    def is_visible(self):
        return self.ec_is_visible()()

    @focused
    def send_keys(self, keys):
        self.elem.send_keys(keys)
    @focused
    def click(self):
        self.elem.click()

    @focused
    def check_inner(self):
        self.inner = self.elem.get_attribute('innerHTML')
        return self.inner
    @focused
    def check_outer(self):
        self.outer = self.elem.get_attribute('outerHTML')
        return self.outer
    def soup(self):
        return BeautifulSoup(self.outer, 'html.parser')


class Tab:
    def __init__(self, browser, window):
        self.window: str = window
        self.browser: Browser = browser
        self.id = {}
        self.cls = {}
        self.css_sel = {}
        self.tag = {}
        self.misc = {}

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
        return self.getElementByTag('html').soup()
    def is_focused(self):
        return self.browser.current_tab() == self.window

    @focused
    def wait_for(self, ecmethod, timeout=6):
        return self.browser.wait_for(ecmethod, timeout)
    @focused
    def wait_for_not(self, ecmethod, timeout=6):
        return self.browser.wait_for_not(ecmethod, timeout)

    @focused
    def open(self, url):
        self.browser.driver.get(url)
    get = go = goto = open

    @focused
    def get_title(self):
        return self.browser.get_title()
    @focused
    def await_title_is(self, title, timeout=5):
        return self.browser.await_title_is(title, timeout)
    @focused
    def await_title_has(self, title, timeout=5):
        return self.browser.await_title_has(title, timeout)
    @focused
    def get_url(self):
        return self.browser.get_url()
    @focused
    def await_url_is(self, url, timeout=5):
        return self.browser.await_url_is(url, timeout)
    @focused
    def await_url_has(self, url, timeout=5):
        return self.browser.await_url_has(url, timeout)

    @focused
    def js(self, js):
        return self.browser.js(js)

    @focused
    def getElementById(self, id, timeout=2, multiple=False):
        e = self.id.get(id, Element(self.browser.getElementById(id, timeout, multiple), self))
        self.id[id] = e
        return e
    @focused
    def getElementByClass(self, cls, timeout=2, multiple=False):
        e = self.cls.get(cls, Element(self.browser.getElementById(cls, timeout, multiple), self))
        self.cls[cls] = e
        return e
    @focused
    def getElementByTag(self, tag, timeout=2, multiple=False):
        e = self.tag.get(tag, Element(self.browser.getElementById(tag, timeout, multiple), self))
        self.tag[tag] = e
        return e
    @focused
    def getElementBySelector(self, css_sel, timeout=2, multiple=False):
        e = self.css_sel.get(css_sel, Element(self.browser.getElementById(css_sel, timeout, multiple), self))
        self.css_sel[css_sel] = e
        return e
    @focused
    def findElement(self, by: By, value, timeout=2, multiple=False):
        e = self.misc.get((by, value), Element(self.browser.findElement(by, value, timeout, multiple), self))
        self.misc[value] = e
        return e

    @focused
    def close(self):
        self.browser.close_tab()
        self.browser.tab_objects.remove(self)
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
        self.profile = FirefoxProfile()

        self.options.headless = False  # Show GUI or not
        # Forces to open new tabs instead of new windows; note that this requires editing selenium/webdriver/firefox/webdriver_prefs.json to move this option from "frozen" to "mutable"
        self.profile.set_preference('browser.link.open_newwindow', 3)
        self.profile.set_preference('browser.link.open_newwindow.restriction', 2)
        # self.profile.set_preference('permissions.default.stylesheet', 2)  # Ignore CSS
        # self.profile.set_preference('permissions.default.image', 2)  # Ignore images

        self.driver = webdriver.Firefox(firefox_profile=self.profile, options=self.options)
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
            t: Tab = self.current_tab_obj()
        return t
    get = open

    def wait_for(self, ecmethod, timeout=6):
        return WebDriverWait(self.driver, timeout).until(ecmethod)
    def wait_for_not(self, ecmethod, timeout=6):
        return WebDriverWait(self.driver, timeout).until_not(ecmethod)
    def confirm(self, ecmethod):
        return ecmethod()
    def confirm_not(self, ecmethod):
        return not ecmethod()

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
    def await_url_has(self, url, timeout=5):
        return self.wait_for(EC.url_contains(url), timeout)
    def get_url(self):
        return self.driver.current_url

    def await_title_is(self, title, timeout=5):
        return self.wait_for(EC.title_is(title), timeout)
    def await_title_has(self, title, timeout=5):
        return self.wait_for(EC.title_contains(title), timeout)
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
    def current_tab_obj(self) -> Tab:
        return self.get_tab_by_key(self.current_tab())
    def await_new_tab(self, timeout=1):
        return self.wait_for(EC.new_window_is_opened(self.driver.window_handles), timeout)
    def _new_tab(self, url=''):
        r = self.js("window.open('{}');".format(url))
        self.switch_last_tab()
        return r
    def new_tab(self, url=None) -> Tab:
        self._new_tab(url)
        t = Tab(self, self.current_tab())
        self.tab_objects.append(t)
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
    def close_tab(self, n=None):
        current = self.current_tab() if n is None else self._get_tab(n)
        tabs = self.driver.window_handles.copy()
        current_index = tabs.index(current)
        tabs.remove(current)
        for tab in self.driver.window_handles:
            if tab != current:
                self.driver.window_handles.remove(tab)
        self.driver.close()
        for tab in tabs:
            self.driver.window_handles.append(tab)

        try:
            _ = self.driver.window_handles[current_index - 1]
            self.switch_tab(current_index - 1)
        except IndexError:
            self.switch_tab(current_index)

    def ec_is_visible(self, obj):
        return EC.visibility_of(obj)
    def ec_is_invisible(self, obj):
        return EC.invisibility_of_element(obj)

    def scroll_to(self, obj):
        r = self.js('return arguments[0].scrollIntoView();', obj)
        self.wait_for(self.ec_is_visible(obj), 3)
        return r

    def js(self, js, *args):
        return self.driver.execute_script(js, *args)

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
        self.driver.quit()


if __name__ == '__main__':
    print('Starting...')
    firefox = Browser()
    blackbaud = firefox.new_tab('https://emeryweiner.myschoolapp.com/app/student#login')

    user = blackbaud.getElementById('Username', 5)
    submit = blackbaud.getElementById('nextBtn')

    user.send_keys('ykey-cohen')
    submit.click()

    pwd = blackbaud.getElementById('Password')
    pwd.send_keys('')

    submit = blackbaud.getElementById('loginBtn')
    submit.click()

    sage = firefox.new_tab('http://www.sagedining.com/menus/emeryweiner')

    blackbaud.await_url_is('https://emeryweiner.myschoolapp.com/app/student#activitystream')
    blackbaud.get('https://emeryweiner.myschoolapp.com/app/student#studentmyday/assignment-center')

    schedule = blackbaud.getElementById('calendar-main-view', 5)
    print(schedule.soup().get_text())
    blackbaud.close()

    menu = sage.getElementById('sageMbDailyViewFrame')
    print(menu.soup().get_text())

    firefox.close()