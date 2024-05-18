from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver

from pytest_logikal.browser.base import BrowserVersion
from pytest_logikal.browser.chromium import ChromiumBrowser
from pytest_logikal.browser.utils import download, make_executable, move, unzip
from pytest_logikal.utils import tmp_path


class Chrome(ChromiumBrowser, WebDriver):
    """
    Google Chrome WebDriver.
    """
    options_class = Options
    service_class = Service


class ChromeVersion(BrowserVersion):
    name = 'chrome'
    driver_class = Chrome

    def install(self) -> None:
        root = f'https://storage.googleapis.com/chrome-for-testing-public/{self.version}/linux64'

        if not self.path.exists():
            self.print(f'Installing Google Chrome {self.version}')
            tmp = tmp_path(self.name)
            unzip(download(f'{root}/chrome-linux64.zip', tmp / 'chrome.zip'))
            move(tmp / 'chrome/chrome-linux64', self.path.parent)
            make_executable(self.path)

        if not self.driver_path.exists():
            self.print(f'Installing Google Chrome WebDriver {self.driver_version}')
            tmp = tmp_path(self.driver_name)
            unzip(download(f'{root}/chromedriver-linux64.zip', tmp / 'chromedriver.zip'))
            move(tmp / 'chromedriver/chromedriver-linux64', self.driver_path.parent)
            make_executable(self.driver_path)
