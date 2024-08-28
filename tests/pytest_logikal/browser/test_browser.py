from dataclasses import replace

from pytest import mark, raises
from pytest_factoryboy import register

from pytest_logikal.browser import Browser, scenarios, set_browser
from pytest_logikal.django import LiveURL
from tests.pytest_logikal import factories
from tests.website.models import User

register(factories.UserFactory)


@set_browser(scenarios.desktop)
def test_single_scenario(browser: Browser) -> None:
    browser.check()


@set_browser([scenarios.desktop, scenarios.mobile_l])
def test_multiple_scenarios(browser: Browser) -> None:
    browser.check()


@set_browser(replace(scenarios.desktop, browsers=['chrome']))
def test_single_browser(browser: Browser) -> None:
    browser.check()


@set_browser(scenarios.Scenario(
    replace(scenarios.desktop.settings, full_page_height=False)  # type: ignore[type-var]
))
def test_not_full_page_height(browser: Browser) -> None:
    browser.get('https://www.sofia.hu/konyv/hamori-zsofia/nincs-ido')
    browser.check()


@set_browser(scenarios.desktop)
def test_browser_check(browser: Browser) -> None:
    browser.get('https://www.sofia.hu/konyv/hamori-zsofia/nincs-ido')
    browser.check('nincs-ido')
    browser.get('https://www.sofia.hu/konyv/hamori-zsofia/perennrose')
    browser.check('perennrose')


@set_browser(scenarios.desktop)
def test_login(live_url: LiveURL, browser: Browser, user: User) -> None:
    browser.get(live_url('internal'))
    browser.check('before_login')

    browser.login(user)
    browser.get(live_url('internal'))
    browser.check('after_login')

    browser.get(live_url('internal', kwargs={'parameter': 'test'}))
    browser.check('after_login_parameter')


@mark.django_db
@set_browser(scenarios.desktop)
def test_login_error(browser: Browser, user: User) -> None:
    with raises(NotImplementedError, match='Only the forced login is implemented'):
        browser.login(user, force=False)
