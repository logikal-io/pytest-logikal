from typing import Any, Callable

import pytest
from django.urls import reverse
from factory import random as factory_random
from mypy_django_plugin import config as mypy_django_plugin_config
from pytest_django.live_server_helper import LiveServer

DEFAULT_RANDOM_SEED = 42
LiveURL = Callable[[str], str]


def pytest_configure(config: pytest.Config) -> None:
    # Patching django-stubs
    def parse_toml_file(self: Any, *_args: Any, **_kwargs: Any) -> None:
        self.django_settings_module = str(config.inicfg['DJANGO_SETTINGS_MODULE'])

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


@pytest.fixture
def live_url(live_server: LiveServer) -> LiveURL:
    """
    Return the path to a URL.
    """
    def live_url_path(name: str) -> str:
        return live_server.url + reverse(name)
    return live_url_path
