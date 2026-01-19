from pytest_logikal import Browser, scenarios, set_browser
from pytest_logikal.django import LiveURL


@set_browser(scenarios.desktop, languages=['en-us'])
def test_single_scenario(browser: Browser, live_url: LiveURL) -> None:
    browser.get(live_url())
    browser.check()
