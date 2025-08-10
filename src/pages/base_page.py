from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BasePage:
    def __init__(self, driver, timeout=15):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def open(self, url):
        self.driver.get(url)

    def find(self, by, selector):
        return self.wait.until(EC.presence_of_element_located((by, selector)))

    def click(self, by, selector):
        el = self.wait.until(EC.element_to_be_clickable((by, selector)))
        el.click()
        return el

    def type(self, by, selector, text, clear=True):
        el = self.find(by, selector)
        if clear:
            el.clear()
        el.send_keys(text)
        return el
