from pytest_logikal import Browser, LiveURL, scenarios, set_browser


@set_browser(scenarios.desktop)
def test_single_scenario(browser: Browser, live_url: LiveURL) -> None:
    browser.get(live_url('index'))
    browser.check()
