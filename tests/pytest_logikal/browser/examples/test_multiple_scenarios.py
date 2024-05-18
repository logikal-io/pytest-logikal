from pytest_django.live_server_helper import LiveServer

from pytest_logikal.browser import Browser, scenarios, set_browser


@set_browser([
    scenarios.desktop,
    scenarios.mobile_l,
])
def test_homepage(browser: Browser, live_server: LiveServer) -> None:
    browser.get(live_server.url)
    browser.check()
