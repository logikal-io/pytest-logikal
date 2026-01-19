from pytest_logikal import Browser, scenarios, set_browser
from pytest_logikal.django import LiveURL


@set_browser([
    scenarios.desktop,
    scenarios.mobile_l,
])
def test_multiple_scenarios(browser: Browser, live_url: LiveURL) -> None:
    browser.get(live_url('index'))
    browser.check()
