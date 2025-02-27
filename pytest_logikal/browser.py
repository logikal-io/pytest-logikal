import inspect
from collections.abc import Iterable, Sequence
from functools import cache
from itertools import product
from operator import itemgetter
from pathlib import Path
from typing import Any

import pytest
from logikal_browser import Browser
from logikal_browser.install import InstalledBrowser, installed_browsers
from logikal_browser.scenarios import Scenario, Settings

from pytest_logikal.utils import Fixture, Function

INSTALLED_BROWSERS_KEY = pytest.StashKey[dict[str, InstalledBrowser]]()


def pytest_sessionstart(session: pytest.Session) -> None:
    session.config.stash[INSTALLED_BROWSERS_KEY] = installed_browsers(
        install=not session.config.getoption('no_install'),
    )


def pytest_report_header(config: pytest.Config) -> str | list[str]:
    browsers = config.stash[INSTALLED_BROWSERS_KEY].values()
    if config.get_verbosity() > 0:
        return ['browsers:'] + [f'  {repr(browser.browser_version)}' for browser in browsers]
    return f'browsers: {', '.join(str(browser.browser_version) for browser in browsers)}'


def check_browser_fixture_request(request: Any) -> None:
    if (
        not hasattr(request, 'param')
        or 'installed_browser' not in request.param
        or 'settings' not in request.param
        or 'headless' not in request.param
    ):
        raise RuntimeError('You must specify a browser scenario for the browser fixture')


@pytest.fixture
def browser(tmp_path: Path, request: Any) -> Iterable[Browser]:  # noqa: D400, D402, D415
    """
    browser() -> logikal_browser.Browser

    Yield a scenario-specific :class:`~logikal_browser.Browser` sub-class instance.
    """
    check_browser_fixture_request(request)

    function = request.node.obj
    if not (source_file := inspect.getsourcefile(function)):  # pragma: no cover, defensive line
        raise RuntimeError(f'Source file cannot be found for "{function}"')
    source_path = Path(source_file)
    screenshot_path = source_path.parent / 'screenshots' / source_path.stem / function.__name__

    installed = request.param['installed_browser']
    with installed.browser_class(
        settings=request.param['settings'],
        version=installed.browser_version,
        headless=request.param['headless'],
        screenshot_path=screenshot_path,
        screenshot_tmp_path=tmp_path,
    ) as driver:
        yield driver


@cache
def get_installed_browsers() -> dict[str, InstalledBrowser]:
    return installed_browsers()


def set_browser(scenarios: Scenario | Sequence[Scenario], headless: bool = True) -> Fixture[Any]:
    """
    Apply the given scenarios to the :func:`~pytest_logikal.browser.browser` fixture.

    Args:
        scenarios: The scenarios to use.
        headless: Whether to use a headless browser instance.

    """
    def parametrized_test_function(function: Function) -> Any:
        argvalues = []
        installed = get_installed_browsers()
        for scenario in ([scenarios] if isinstance(scenarios, Scenario) else scenarios):
            browsers = scenario.browsers or installed.keys()
            settings = scenario.settings
            if isinstance(settings, Settings):
                settings = [settings]
            for browser_name, settings in product(browsers, settings):
                argvalues.append({
                    'name': f'{browser_name}_{settings.name}',
                    'installed_browser': installed[browser_name],
                    'settings': settings,
                    'headless': headless,
                })

        return pytest.mark.parametrize(
            argnames='browser', argvalues=argvalues, indirect=True, ids=itemgetter('name'),
        )(function)

    return parametrized_test_function
