from pytest_logikal import Browser, LiveURL, scenarios, set_browser


@set_browser([scenarios.desktop, scenarios.mobile_l], languages=['en-us', 'en-gb'])
def test_multiple_scenarios(browser: Browser, live_url: LiveURL) -> None:
    browser.get(live_url('index'))
    browser.check()
