from dataclasses import replace
from pathlib import Path
from zipfile import ZipFile

from pytest_mock import MockerFixture

from pytest_logikal.browser import Browser, scenarios, set_browser
from pytest_logikal.browser.base import BrowserVersion
from pytest_logikal.browser.chrome import ChromeVersion


def test_install(mocker: MockerFixture, tmp_path: Path) -> None:
    mocker.patch('pytest_logikal.browser.chrome.tmp_path', return_value=tmp_path)
    mocker.patch('pytest_logikal.browser.base.BrowserVersion.created')

    browser_zip_path = tmp_path / 'chrome.zip'
    with ZipFile(browser_zip_path, 'w') as browser_zip:
        browser_zip.writestr('chrome-linux64/chrome', data='')

    driver_zip_path = tmp_path / 'chromedriver.zip'
    with ZipFile(driver_zip_path, 'w') as driver_zip:
        driver_zip.writestr('chromedriver-linux64/chromedriver', data='')

    mocker.patch('pytest_logikal.browser.chrome.download', side_effect=[
        browser_zip_path,
        driver_zip_path,
    ])
    version = ChromeVersion(version='test version', install_path=tmp_path / 'install')
    assert version.path.exists()
    assert version.driver_path.exists()


@set_browser(replace(scenarios.desktop, browsers=['chrome']))
def test_installed_version(browser: Browser) -> None:
    assert browser.capabilities['browserVersion'] == BrowserVersion.created['chrome'].version
