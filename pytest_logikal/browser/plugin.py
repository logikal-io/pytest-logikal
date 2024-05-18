import inspect
from itertools import product
from operator import itemgetter
from pathlib import Path
from typing import Any, Iterable, List, Union

import pytest
from logikal_utils.project import PYPROJECT

from pytest_logikal.browser.base import Browser, BrowserVersion
from pytest_logikal.browser.chrome import ChromeVersion
from pytest_logikal.browser.edge import EdgeVersion
from pytest_logikal.browser.scenarios import Scenario, Settings
from pytest_logikal.utils import Fixture, Function


def pytest_sessionstart(session: pytest.Session) -> None:
    if not (versions := PYPROJECT.get('tool', {}).get('browser', {}).get('versions', {})):
        raise RuntimeError('You must specify at least one browser version')

    install = not session.config.getoption('no_install')
    for browser_name, version in versions.items():
        if browser_name == 'chrome':
            ChromeVersion(version=version, install=install)
        elif browser_name == 'edge':
            EdgeVersion(version=version, install=install)
        else:
            raise RuntimeError(f'Browser "{browser_name}" is currently not supported')

    BrowserVersion.final_info()


def pytest_report_header(config: pytest.Config) -> Union[str, List[str]]:
    browsers = [item[1] for item in sorted(BrowserVersion.created.items())]
    if config.get_verbosity() > 0:
        return ['browsers:'] + [f'  {repr(browser)}' for browser in browsers]
    return f'browsers: {", ".join(str(browser) for browser in browsers)}'


def check_browser_fixture_request(request: Any) -> None:
    if (
        not hasattr(request, 'param')
        or 'version' not in request.param
        or 'settings' not in request.param
    ):
        raise RuntimeError('You must specify a browser scenario for the browser fixture')


@pytest.fixture
def browser(tmp_path: Path, request: Any) -> Iterable[Browser]:  # noqa: D400, D402, D415
    """
    browser() -> Browser

    Yield a scenario-specific :class:`~pytest_logikal.browser.Browser` sub-class instance.
    """
    check_browser_fixture_request(request)

    function = request.node.obj
    if not (source_file := inspect.getsourcefile(function)):  # pragma: no cover, defensive line
        raise RuntimeError(f'Source file cannot be found for "{function}"')
    source_path = Path(source_file)
    screenshot_path = source_path.parent / 'screenshots' / source_path.stem / function.__name__

    with request.param['version'].driver(
        settings=request.param['settings'],
        screenshot_path=screenshot_path, image_tmp_path=tmp_path,
    ) as driver:
        yield driver


def set_browser(scenarios: Union[Scenario, List[Scenario]]) -> Fixture[Any]:
    """
    Apply the given scenarios to the :func:`~pytest_logikal.browser.plugin.browser` fixture.

    Args:
        scenarios: The scenarios to use.

    """
    def parametrized_test_function(function: Function) -> Any:
        argvalues = []
        for scenario in ([scenarios] if isinstance(scenarios, Scenario) else scenarios):
            browsers = scenario.browsers or BrowserVersion.created.keys()
            settings = scenario.settings
            if isinstance(settings, Settings):
                settings = [settings]
            for browser_name, settings in product(browsers, settings):
                argvalues.append({
                    'name': f'{browser_name}_{settings.name}',
                    'version': BrowserVersion.created[browser_name],
                    'settings': settings,
                })

        return pytest.mark.parametrize(
            argnames='browser', argvalues=argvalues, indirect=True, ids=itemgetter('name'),
        )(function)

    return parametrized_test_function
