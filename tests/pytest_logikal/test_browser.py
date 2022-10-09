from importlib import reload
from pathlib import Path

from faker.proxy import Faker
from pytest import raises
from pytest_mock.plugin import MockerFixture
from selenium.common.exceptions import SessionNotCreatedException

from pytest_logikal import browser as pytest_logikal_browser
from pytest_logikal.browser import Browser, set_browser

pytest_logikal_browser = reload(pytest_logikal_browser)  # ensures coverage captures definitions


def test_faker_seed(faker: Faker) -> None:
    assert faker.name() == 'Allison Hill'


def test_browser_chromedriver_version_error(tmp_path: Path, mocker: MockerFixture) -> None:
    mocker.patch('pytest_logikal.browser.Chrome', side_effect=SessionNotCreatedException(
        'This version of ChromeDriver only supports Chrome version 1\n'
        'Current browser version is 2 with binary path'
    ))
    with raises(RuntimeError, match='Invalid ChromeDriver version'):
        Browser(temp_path=tmp_path)

    mocker.patch('pytest_logikal.browser.Chrome', side_effect=SessionNotCreatedException('Error'))
    with raises(SessionNotCreatedException, match='Error'):
        Browser(temp_path=tmp_path)


def test_set_browser_source_path_error(mocker: MockerFixture) -> None:
    mocker.patch('pytest_logikal.browser.inspect.getsourcefile', return_value=None)
    with raises(RuntimeError, match='Source file cannot be found'):
        set_browser()(lambda: None)


@set_browser(width=1800, height=800)
def test_single_browser(browser: Browser) -> None:
    browser.check()


@set_browser(
    dict(width=1800, height=900),
    dict(name='tablet', width=1100, height=700, mobile=True),
    dict(name='mobile', width=480, height=800, mobile=True),
)
def test_multiple_browsers(browser: Browser) -> None:
    browser.check()


@set_browser(name='desktop', width=1800)
def test_browser_check(browser: Browser) -> None:
    browser.get('https://www.sofia.hu/konyv/hamori-zsofia/nincs-ido')
    browser.check('nincs-ido')
    browser.get('https://www.sofia.hu/konyv/hamori-zsofia/perennrose')
    browser.check('perennrose')
