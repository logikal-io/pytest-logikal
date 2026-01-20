import inspect
from collections.abc import Iterable
from contextlib import AbstractContextManager, nullcontext
from dataclasses import replace
from functools import cache
from itertools import product
from logging import getLogger
from operator import itemgetter
from pathlib import Path
from typing import Any

import pytest
from logikal_browser import Browser
from logikal_browser.install import InstalledBrowser, installed_browsers
from logikal_browser.scenarios import Scenario, Settings

from pytest_logikal.core import EXTRAS
from pytest_logikal.utils import Fixture, Function

logger = getLogger(__name__)

__all__ = ['Browser', 'set_browser']

_INSTALLED_BROWSERS_KEY = pytest.StashKey[dict[str, InstalledBrowser]]()


def pytest_sessionstart(session: pytest.Session) -> None:
    session.config.stash[_INSTALLED_BROWSERS_KEY] = installed_browsers(
        install=not session.config.getoption('no_install'),
    )


def pytest_report_header(config: pytest.Config) -> str | list[str]:
    browsers = config.stash[_INSTALLED_BROWSERS_KEY].values()
    if config.get_verbosity() > 0:
        return ['browsers:'] + [f'  {repr(browser.browser_version)}' for browser in browsers]
    return f'browsers: {', '.join(str(browser.browser_version) for browser in browsers)}'


@cache
def _get_installed_browsers() -> dict[str, InstalledBrowser]:
    return installed_browsers()


def _get_scenarios(scenarios: Scenario | Iterable[Scenario]) -> Iterable[Scenario]:
    return [scenarios] if isinstance(scenarios, Scenario) else scenarios


def _get_settings(settings: Settings | Iterable[Settings]) -> Iterable[Settings]:
    return [settings] if isinstance(settings, Settings) else settings


def _get_languages(scenario_languages: Iterable[str] | None) -> Iterable[str] | Iterable[None]:
    # Use the scenario languages if Django is installed
    if scenario_languages:
        if not EXTRAS['django']:
            raise RuntimeError('The `django` extra must be installed for scenario languages')
        return scenario_languages

    # Use Django's configured languages if available
    if EXTRAS['django']:
        from django.conf import settings  # pylint: disable=import-outside-toplevel

        return [language_code for language_code, _ in settings.LANGUAGES]

    # Return `None` as a default
    return [None]


def _check_browser_fixture_request(request: Any) -> None:
    if (
        not hasattr(request, 'param')
        or 'installed_browser' not in request.param
        or 'settings' not in request.param
        or 'language' not in request.param
    ):
        raise RuntimeError('You must specify a browser scenario for the browser fixture')


def _language_context(language: str | None) -> AbstractContextManager[Any]:
    if not language:
        return nullcontext()

    if not EXTRAS['django']:
        raise RuntimeError('The `django` extra must be installed for browser languages')

    from django.utils import translation  # pylint: disable=import-outside-toplevel

    logger.debug(f'Setting the language to "{language}"')
    return translation.override(language)


@pytest.fixture
def browser(tmp_path: Path, request: Any) -> Iterable[Browser]:  # noqa: D400, D402, D415
    """
    browser() -> logikal_browser.Browser

    Yield a scenario-specific :class:`~logikal_browser.Browser` sub-class instance.
    """
    _check_browser_fixture_request(request)

    function = request.node.obj
    if not (source_file := inspect.getsourcefile(function)):  # pragma: no cover, defensive line
        raise RuntimeError(f'Source file cannot be found for "{function}"')
    source_path = Path(source_file)
    screenshot_path = source_path.parent / 'screenshots' / source_path.stem / function.__name__
    installed = request.param['installed_browser']
    language = request.param['language']
    with _language_context(language=language):
        with installed.browser_class(
            settings=request.param['settings'],
            version=installed.browser_version,
            language=language,
            screenshot_path=screenshot_path,
            screenshot_tmp_path=tmp_path,
        ) as driver:
            yield driver


def set_browser(
    scenarios: Scenario | Iterable[Scenario],
    languages: Iterable[str] | None = None,
    headless: bool | None = None,
) -> Fixture[Any]:
    """
    Apply the given scenarios to the :func:`~pytest_logikal.browser.browser` fixture.

    Args:
        scenarios: The scenarios to use.
        languages: The languages to use. Defaults to using the scenario languages.
        headless: Whether to use a headless browser instance.

    """
    def parametrized_test_function(function: Function) -> Any:
        argvalues = []
        installed = _get_installed_browsers()
        for scenario in _get_scenarios(scenarios):
            for settings, language, browser_name in product(
                _get_settings(scenario.settings),
                _get_languages(languages or scenario.languages),
                scenario.browsers or installed.keys(),
            ):
                name_parts = [settings.name, language, browser_name]
                argvalues.append({
                    'name': '-'.join(part for part in name_parts if part is not None),
                    'installed_browser': installed[browser_name],
                    'settings': settings if not headless else replace(settings, headless=headless),
                    'language': language,
                })

        return pytest.mark.parametrize(
            argnames='browser', argvalues=argvalues, indirect=True, ids=itemgetter('name'),
        )(function)

    return parametrized_test_function
