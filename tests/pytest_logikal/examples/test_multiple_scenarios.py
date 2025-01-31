from logikal_browser import Browser, scenarios
from pytest_django.live_server_helper import LiveServer

from pytest_logikal.browser import set_browser


@set_browser([
    scenarios.desktop,
    scenarios.mobile_l,
])
def test_multiple_scenarios(browser: Browser, live_server: LiveServer) -> None:
    browser.get(live_server.url)
    browser.check()
