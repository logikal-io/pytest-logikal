from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any, Callable, Optional

import pytest
from django.conf import settings
from django.urls import reverse
from django_migration_linter import MigrationLinter
from django_migration_linter.management.commands import lintmigrations
from factory import random as factory_random
from mypy_django_plugin import config as mypy_django_plugin_config
from pytest_django.live_server_helper import LiveServer
from pytest_django.plugin import _blocking_manager  # pylint: disable=import-private-name

from pytest_logikal.core import PYPROJECT, ReportInfoType
from pytest_logikal.plugin import Item, ItemRunError, Plugin

DEFAULT_RANDOM_SEED = 42
LiveURL = Callable[[str], str]


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'migrations: checks Django migrations.')
    if config.option.django:
        config.pluginmanager.register(MigrationPlugin(config=config))

    # Patching django-stubs
    def parse_toml_file(self: Any, *_args: Any, **_kwargs: Any) -> None:
        self.django_settings_module = str(config.inicfg['DJANGO_SETTINGS_MODULE'])

    mypy_django_plugin_config.DjangoPluginConfig.parse_toml_file = parse_toml_file  # type: ignore


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup('django')
    group.addoption('--django', action='store_true', default=False,
                    help='run django migration checks')


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
def live_url(live_server: LiveServer) -> LiveURL:  # noqa: D400,D402,D415,D417
    """
    live_url(name: str) -> str

    Return the path to a URL.

    Args:
        name: The URL pattern name.

    """
    def live_url_path(name: str) -> str:
        return live_server.url + reverse(name)
    return live_url_path


class MigrationItem(Item):
    def runtest(self, migrations_file_path: Optional[Path] = None) -> None:
        # We cannot request a fixture here, so we use the blocking manager directly
        # See https://github.com/pytest-dev/pytest/discussions/10915
        with _blocking_manager.unblock():
            linter = MigrationLinter(**{
                'all_warnings_as_errors': True,
                **getattr(settings, 'MIGRATION_LINTER_OPTIONS', {}),
                **PYPROJECT.get('tool', {}).get(lintmigrations.CONFIG_NAME, {}),
            })
            with redirect_stdout(StringIO()) as code_stdout:
                linter.lint_all_migrations(migrations_file_path=migrations_file_path)
            migrations = 'migration' if linter.nb_total == 1 else 'migrations'
            print(f'Checked {linter.nb_total} {migrations} ({linter.nb_ignored} ignored)')
            if linter.nb_warnings or linter.nb_erroneous:
                raise ItemRunError(code_stdout.getvalue().rstrip())

    def reportinfo(self) -> ReportInfoType:
        return (self.path, None, f'[{MigrationPlugin.name}]')


class MigrationPlugin(Plugin):
    name = 'migrations'
    item = MigrationItem
