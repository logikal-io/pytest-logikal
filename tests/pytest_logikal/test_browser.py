from pathlib import Path

from pytest import mark, raises
from pytest_factoryboy import register
from pytest_mock.plugin import MockerFixture
from selenium.common.exceptions import SessionNotCreatedException

from pytest_logikal.browser import Browser, BrowserSettings, set_browser
from pytest_logikal.django import LiveURL
from tests.pytest_logikal import factories
from tests.website.models import User

register(factories.UserFactory)


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


def test_default_browser(browser: Browser) -> None:
    browser.check()


@set_browser(setting='tablet')
def test_single_browser(browser: Browser) -> None:
    browser.check()


@set_browser(
    dict(setting='desktop'),
    dict(setting='mobile-l'),
)
def test_multiple_browsers(browser: Browser) -> None:
    browser.check()


@set_browser(setting='desktop-docs')
def test_fixed_browser_setting(browser: Browser) -> None:
    browser.check()


@set_browser(setting='mobile-xl')
def test_custom_setting(browser: Browser) -> None:
    browser.check()


@set_browser(name='laptop-xl', width=1920, height=1080)
def test_inline_setting(browser: Browser) -> None:
    browser.check()


@set_browser(height='frame')
def test_frame_height(browser: Browser) -> None:
    browser.get('https://www.sofia.hu/konyv/hamori-zsofia/nincs-ido')
    browser.check()


@set_browser(setting='desktop', height=940)
def test_overridden_setting(browser: Browser) -> None:
    browser.check()


def test_browser_check(browser: Browser) -> None:
    browser.get('https://www.sofia.hu/konyv/hamori-zsofia/nincs-ido')
    browser.check('nincs-ido')
    browser.get('https://www.sofia.hu/konyv/hamori-zsofia/perennrose')
    browser.check('perennrose')


def test_login(live_url: LiveURL, browser: Browser, user: User) -> None:
    browser.get(live_url('internal'))
    browser.check('before_login')

    browser.login(user)
    browser.get(live_url('internal'))
    browser.check('after_login')


@mark.django_db
def test_login_error(browser: Browser, user: User) -> None:
    with raises(NotImplementedError, match='Only the forced login is implemented'):
        browser.login(user, force=False)


def test_unknown_browser_setting() -> None:
    with raises(ValueError, match='Unknown browser setting'):
        BrowserSettings('non-existent')


def test_missing_setting() -> None:
    with raises(ValueError, match='setting "width" must be specified'):
        BrowserSettings(setting=None)
