try:
    import zoneinfo  # type: ignore[import-not-found]
except ImportError:
    from backports import zoneinfo  # note: this is built-in after Python 3.9+
from typing import Any, Dict, Iterable, Optional, Protocol, Sequence

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone as django_timezone, translation
from factory import random as factory_random
from logikal_utils.random import DEFAULT_RANDOM_SEED
from mypy_django_plugin import config as mypy_django_plugin_config
from pytest_django.live_server_helper import LiveServer

from pytest_logikal.node_install import install_node_packages
from pytest_logikal.utils import Fixture, Function
from pytest_logikal.validator import Validator


def pytest_sessionstart(session: pytest.Session) -> None:
    if not session.config.getoption('no_install'):
        install_node_packages()

    css_or_svg = not session.config.getoption('no_css') or not session.config.getoption('no_svg')
    if not session.config.getoption('fast') and css_or_svg:
        # We start the validator service here to avoid pytest's output capturing
        Validator.service_url()


def pytest_configure(config: pytest.Config) -> None:
    # Patching django-stubs
    def parse_toml_file(self: Any, *_args: Any, **_kwargs: Any) -> None:
        self.django_settings_module = str(config.inicfg['DJANGO_SETTINGS_MODULE'])
        self.strict_settings = True

    mypy_django_plugin_config.DjangoPluginConfig.parse_toml_file = parse_toml_file  # type: ignore


@pytest.fixture(scope='session', autouse=True)
def faker_seed() -> int:
    """
    Set a default seed for Faker for deterministic testing. Automatically applied.
    """
    return DEFAULT_RANDOM_SEED


@pytest.fixture(scope='function', autouse=True)
def factory_seed() -> None:
    """
    Set a default seed for pytest-factoryboy for deterministic testing. Automatically applied.
    """
    factory_random.reseed_random(DEFAULT_RANDOM_SEED)


class LiveURL(Protocol):
    def __call__(
        self,
        name: Optional[str] = None,
        args: Optional[Sequence[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> str:
        ...


@pytest.fixture
def live_url(live_server: LiveServer) -> LiveURL:  # noqa: D400, D402, D415, D417
    """
    live_url(name: str | None, args: Sequence[Any] | None, kwargs: Dict[str, Any] | None) -> str

    Return the path to a URL.

    Args:
        name: The URL pattern name.
        args: The URL arguments to use.
        kwargs: The URL keyword arguments to use.

    """
    def live_url_path(
        name: Optional[str] = None,
        args: Optional[Sequence[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> str:
        return live_server.url + (reverse(viewname=name, args=args, kwargs=kwargs) if name else '')
    return live_url_path


@pytest.fixture
def language(request: Any) -> Iterable[str]:
    """
    Return the currently activated language.
    """
    if language_code := getattr(request, 'param', None):
        with translation.override(language_code):
            yield language_code
    else:
        yield translation.get_language()


def set_language(*language_codes: str) -> Fixture[Any]:
    """
    Mark a test to run with each of the specified languages.

    Args:
        *language_codes: The language codes to use.

    .. note:: You must also use the :func:`language <pytest_logikal.django.language>` fixture in
        your test when applying this decorator.

    """
    def parametrized_test_function(function: Function) -> Any:
        return pytest.mark.parametrize(
            argnames='language', argvalues=language_codes, indirect=True,
            ids=lambda value: f'language={value}'
        )(function)
    return parametrized_test_function


def all_languages() -> Fixture[Any]:
    """
    Mark a test to run with every available language.

    .. note:: You must also use the :func:`language <pytest_logikal.django.language>` fixture in
        your test when applying this decorator.

    """
    return set_language(*(language_code for language_code, _ in settings.LANGUAGES))


@pytest.fixture
def timezone(request: Any) -> Iterable[str]:
    """
    Return the current time zone ID.
    """
    if zone_id := getattr(request, 'param', None):
        current_timezone = django_timezone.get_current_timezone()
        django_timezone.activate(zoneinfo.ZoneInfo(zone_id))
        yield zone_id
        django_timezone.activate(current_timezone)
    else:
        yield django_timezone.get_current_timezone_name()


def set_timezone(*zone_ids: str) -> Fixture[Any]:
    """
    Mark a test to run with each of the specified time zones.

    Args:
        *zone_ids: The time zone IDs to use.

    .. note:: You must also use the :func:`timezone <pytest_logikal.django.timezone>` fixture in
        your test when applying this decorator.

    """
    def parametrized_test_function(function: Function) -> Any:
        return pytest.mark.parametrize(
            argnames='timezone', argvalues=zone_ids, indirect=True,
            ids=lambda value: f'timezone={value}'
        )(function)
    return parametrized_test_function
